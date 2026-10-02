#!/usr/bin/env python3
"""
Warehouse Priority Engine - FastAPI microservice
================================================
Wraps warehouse_priority_engine.py (must sit next to this file, unchanged).

Run:    uvicorn app:app --host 0.0.0.0 --port 8000
Docs:   http://localhost:8000/docs   (interactive Swagger UI)

Endpoints
---------
GET  /health                  liveness
GET  /v1/config/defaults      engine defaults (all assumptions)
POST /v1/priorities/rank      stateless "which task next?"  (one decision, one picker)
POST /v1/simulate             run the dynamic simulation on JSON dispatches
POST /v1/simulate/dataset     run the original CSV pipeline from an uploaded .zip

Timestamps: ISO-8601. Naive timestamps are used as-is; tz-aware ones are converted to UTC.
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import shutil
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from typing import Literal, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, model_validator

import warehouse_priority_engine as eng

MAX_TASKS = int(os.getenv("MAX_TASKS", "20000"))        
MAX_WAVES = int(os.getenv("MAX_WAVES", "1000"))

Policy = Literal["priority", "fifo", "nearest"]

app = FastAPI(title="Warehouse Priority Engine", version="1.0.0",
              description="Dynamic urgency-aware picking priority engine (V1 scheduler, not ML).")


# ════════════════════════════════════════════════════════════════════════════
# SHARED MODELS
# ════════════════════════════════════════════════════════════════════════════
class Position(BaseModel):
    x: float
    y: float
    z: float = 1.0


class Weights(BaseModel):
    urgency: float = Field(0.40, ge=0)
    quantity: float = Field(0.25, ge=0)
    complexity: float = Field(0.20, ge=0)
    distance: float = Field(0.15, ge=0)


class ConfigIn(BaseModel):
    """Every field optional; omitted fields keep the engine default. All are assumptions, not measurements."""
    sla_minutes: Optional[float] = Field(None, gt=0, description="deadline = creation + SLA (only used if a deadline is not supplied)")
    picker_speed_mps: Optional[float] = Field(None, gt=0)
    unit_pick_time_sec: Optional[float] = Field(None, ge=0)
    coord_unit_to_meters: Optional[float] = Field(None, gt=0)
    z_weight: Optional[float] = Field(None, ge=0)
    tier_urgent_max_slack_min: Optional[float] = None
    tier_high_max_slack_min: Optional[float] = None
    slack_horizon_min: Optional[float] = Field(None, gt=0)
    weights: Optional[Weights] = None


_CFG_MAP = {
    "sla_minutes": "SIMULATED_DISPATCH_SLA_MINUTES",
    "picker_speed_mps": "PICKER_SPEED_MPS",
    "unit_pick_time_sec": "UNIT_PICK_TIME_SEC",
    "coord_unit_to_meters": "COORD_UNIT_TO_METERS",
    "z_weight": "Z_WEIGHT",
    "tier_urgent_max_slack_min": "TIER_URGENT_MAX_SLACK_MIN",
    "tier_high_max_slack_min": "TIER_HIGH_MAX_SLACK_MIN",
    "slack_horizon_min": "SLACK_HORIZON_MIN",
}


def build_config(c: Optional[ConfigIn]) -> eng.Config:
    cfg = eng.Config()
    if c is not None:
        for k, v in c.model_dump(exclude_none=True).items():
            if k == "weights":
                cfg.W_URGENCY, cfg.W_QUANTITY = v["urgency"], v["quantity"]
                cfg.W_COMPLEXITY, cfg.W_DISTANCE = v["complexity"], v["distance"]
            else:
                setattr(cfg, _CFG_MAP[k], v)
    if cfg.TIER_URGENT_MAX_SLACK_MIN >= cfg.TIER_HIGH_MAX_SLACK_MIN:
        raise HTTPException(422, "tier_urgent_max_slack_min must be < tier_high_max_slack_min")
    return cfg


def naive(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def clean(o):
    """Make numpy scalars / NaN JSON-safe."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.generic):
        o = o.item()
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o


def records(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient="records", date_format="iso"))


# ════════════════════════════════════════════════════════════════════════════
# POST /v1/priorities/rank   (stateless single decision)
# ════════════════════════════════════════════════════════════════════════════
class RankTask(BaseModel):
    task_id: str
    dispatch_id: str
    location: Optional[str] = Field(None, description="location label; used to count distinct locations per dispatch")
    x: float
    y: float
    z: float = 1.0
    remaining_quantity: int = Field(gt=0)
    deadline: datetime = Field(description="dispatch deadline")


class RankRequest(BaseModel):
    now: datetime
    picker_position: Position = Position(x=0, y=0, z=1)
    tasks: list[RankTask] = Field(min_length=1)
    config: Optional[ConfigIn] = None

    @model_validator(mode="after")
    def _unique(self):
        ids = [t.task_id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("task_id values must be unique")
        return self


@app.post("/v1/priorities/rank", summary="Rank open tasks and return the next one to pick")
def rank(req: RankRequest):
    if len(req.tasks) > MAX_TASKS:
        raise HTTPException(413, f"max {MAX_TASKS} tasks per request")
    cfg = build_config(req.config)
    now = naive(req.now)
    T = req.tasks
    n = len(T)

    deadline_s = np.array([(naive(t.deadline) - now).total_seconds() for t in T])
    remaining = np.array([t.remaining_quantity for t in T], dtype=float)
    x, y, z = (np.array([getattr(t, k) for t in T], dtype=float) for k in "xyz")
    d_code = pd.factorize([t.dispatch_id for t in T])[0]
    l_code = pd.factorize([t.location or f"{t.x}:{t.y}:{t.z}" for t in T])[0]
    p = req.picker_position

    ev = eng.PriorityEngine(cfg).evaluate(0.0, (p.x, p.y, p.z), deadline_s, remaining, x, y, z, d_code, l_code)
    order = np.lexsort((np.arange(n), -ev.score, ev.tier))      # tier asc, score desc, input order

    ranking = [{
        "rank": r + 1,
        "task_id": T[i].task_id,
        "dispatch_id": T[i].dispatch_id,
        "priority_level": eng.TIER_NAMES[ev.tier[i]],
        "priority_score": round(float(ev.score[i]), 4),
        "slack_min": round(float(ev.slack_min[i]), 2),
        "travel_distance_m": round(float(ev.travel_m[i]), 2),
        "travel_time_sec": round(float(ev.travel_s[i]), 2),
        "pick_time_sec": round(float(ev.pick_s[i]), 2),
        "estimated_total_time_min": round(float(ev.total_s[i] / 60), 2),
    } for r, i in enumerate(order)]

    return clean({
        "evaluated_at": now.isoformat(),
        "next_task": ranking[0],
        "ranking": ranking,
        "note": "priority_score is normalised inside this request - only compare scores within the same tier/request.",
    })


# ════════════════════════════════════════════════════════════════════════════
# POST /v1/simulate   (JSON dispatches -> full simulation)
# ════════════════════════════════════════════════════════════════════════════
class SimTask(BaseModel):
    task_id: Optional[str] = None
    reference: str
    size: float = 0.0
    quantity: int = Field(gt=0)
    location: Optional[str] = None
    x: float
    y: float
    z: float = 1.0
    operator: str = Field("OP-1", description="the picker that owns this task")


class SimDispatch(BaseModel):
    dispatch_id: str
    creation_time: datetime
    deadline: Optional[datetime] = Field(None, description="default = creation_time + config.sla_minutes")
    tasks: list[SimTask] = Field(min_length=1)


class SimRequest(BaseModel):
    dispatches: list[SimDispatch] = Field(min_length=1)
    depot: Position = Position(x=0, y=0, z=1)
    policies: list[Policy] = Field(["priority"], min_length=1,
                                   description="first policy supplies the log/dispatch output; all get KPIs")
    include_execution_log: bool = True
    config: Optional[ConfigIn] = None

    @model_validator(mode="after")
    def _unique(self):
        dids = [d.dispatch_id for d in self.dispatches]
        if len(dids) != len(set(dids)):
            raise ValueError("dispatch_id values must be unique")
        tids = [t.task_id for d in self.dispatches for t in d.tasks if t.task_id]
        if len(tids) != len(set(tids)):
            raise ValueError("task_id values must be unique")
        return self


def tasks_from_request(req: SimRequest, cfg: eng.Config) -> pd.DataFrame:
    rows, seq = [], 0
    for d in req.dispatches:
        created = naive(d.creation_time)
        deadline = naive(d.deadline) if d.deadline else created + pd.Timedelta(minutes=cfg.SIMULATED_DISPATCH_SLA_MINUTES)
        for j, t in enumerate(d.tasks, 1):
            seq += 1
            rows.append(dict(
                task_id=t.task_id or f"{d.dispatch_id}-{j}", dispatch_id=d.dispatch_id,
                reference=t.reference, size=float(t.size), quantity_required=t.quantity,
                quantity_picked=0, remaining_quantity=t.quantity,
                location=t.location or f"{t.x}:{t.y}:{t.z}", x=t.x, y=t.y, z=t.z,
                operator=t.operator, creation_time=created, dispatch_deadline=deadline, pick_seq=seq))
    df = pd.DataFrame(rows)
    df["creation_time"] = pd.to_datetime(df["creation_time"])
    df["dispatch_deadline"] = pd.to_datetime(df["dispatch_deadline"])
    if not df.task_id.is_unique:
        raise HTTPException(422, "generated/supplied task_id values are not unique")
    return df.sort_values(["creation_time", "pick_seq"], kind="stable").reset_index(drop=True)


def run_policies(tasks: pd.DataFrame, cfg: eng.Config, policies: list[str], depot) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    kp, first = {}, None
    for pol in dict.fromkeys(policies):                       # de-dupe, keep order
        try:
            L, D, state = eng.simulate(tasks, cfg, pol, depot)
            eng.verify_simulation(tasks, L, D, state)         # conservation checks
        except AssertionError as e:
            raise HTTPException(500, f"simulation integrity check failed ({pol}): {e}")
        kp[pol] = eng.kpis(L, D)
        if first is None:
            first = (L, D)
    return kp, first[0], first[1]


def format_log(L: pd.DataFrame) -> list[dict]:
    cols = ["task_id", "operator", "start_time", "end_time", "travel_m", "travel_s", "pick_s",
            "tier_at_pick", "score_at_pick", "slack_min_at_pick", "open_tasks"]
    out = L[cols].copy()
    out[["travel_m", "travel_s", "pick_s", "slack_min_at_pick"]] = out[["travel_m", "travel_s", "pick_s", "slack_min_at_pick"]].round(2)
    out["score_at_pick"] = out["score_at_pick"].round(4)
    return records(out.sort_values(["start_time", "operator"]))


def format_dispatches(D: pd.DataFrame) -> list[dict]:
    out = D.copy()
    out[["lateness_min", "flow_time_min"]] = out[["lateness_min", "flow_time_min"]].round(2)
    return records(out)


@app.post("/v1/simulate", summary="Run the dynamic picking simulation on JSON dispatches")
def simulate(req: SimRequest):
    n = sum(len(d.tasks) for d in req.dispatches)
    if n > MAX_TASKS:
        raise HTTPException(413, f"max {MAX_TASKS} tasks per request (got {n})")
    cfg = build_config(req.config)
    tasks = tasks_from_request(req, cfg)
    t0 = time.time()
    kp, L, D = run_policies(tasks, cfg, req.policies, (req.depot.x, req.depot.y, req.depot.z))
    body = {
        "summary": {"tasks": len(tasks), "dispatches": int(tasks.dispatch_id.nunique()),
                    "units": int(tasks.quantity_required.sum()), "operators": int(tasks.operator.nunique()),
                    "policy_for_details": req.policies[0], "runtime_sec": round(time.time() - t0, 3)},
        "kpis": kp,
        "dispatch_summary": format_dispatches(D),
    }
    if req.include_execution_log:
        body["execution_log"] = format_log(L)
    return clean(body)


# ════════════════════════════════════════════════════════════════════════════
# POST /v1/simulate/dataset   (original CSV pipeline, .zip upload)
# ════════════════════════════════════════════════════════════════════════════
@app.post("/v1/simulate/dataset", summary="Upload the dataset .zip and run the original CSV pipeline")
def simulate_dataset(
    file: UploadFile = File(..., description="zip containing Customer_Order.csv, Picking_Wave.csv, Product.csv, "
                                              "Storage_Location.csv, Support_Points_Navigation.csv"),
    max_waves: int = Query(300, ge=1, le=MAX_WAVES),
    start: Optional[str] = Query(None, description="YYYY-MM-DD inclusive"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD exclusive"),
    policies: list[Policy] = Query(["priority"]),
    sla_minutes: Optional[float] = Query(None, gt=0),
    picker_speed_mps: Optional[float] = Query(None, gt=0),
    unit_pick_time_sec: Optional[float] = Query(None, ge=0),
    coord_unit_to_meters: Optional[float] = Query(None, gt=0),
    include_execution_log: bool = False,
):
    cfg = build_config(ConfigIn(sla_minutes=sla_minutes, picker_speed_mps=picker_speed_mps,
                                unit_pick_time_sec=unit_pick_time_sec, coord_unit_to_meters=coord_unit_to_meters))
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp.close()
        if not zipfile.is_zipfile(tmp.name):
            raise HTTPException(400, "upload must be a .zip file")
        try:
            raw = eng.load_raw(tmp.name)
        except Exception as e:
            raise HTTPException(422, f"could not read dataset: {type(e).__name__}: {e}")

        joins = eng.validate_joins(raw, cfg)
        tasks = eng.build_task_table(raw, cfg, max_waves, start, end)
        if tasks.empty:
            raise HTTPException(422, "no tasks found for the selected period/waves")
        if len(tasks) > MAX_TASKS:
            raise HTTPException(413, f"{len(tasks)} tasks exceeds MAX_TASKS={MAX_TASKS}; lower max_waves")
        lk = eng._location_lookup(raw, cfg)
        depot = tuple(lk[lk.location == cfg.DEPOT_LOCATION].iloc[0][["x", "y", "z"]].astype(float))

        t0 = time.time()
        kp, L, D = run_policies(tasks, cfg, policies, depot)
        body = {
            "summary": {"tasks": len(tasks), "dispatches": int(tasks.dispatch_id.nunique()),
                        "units": int(tasks.quantity_required.sum()), "operators": int(tasks.operator.nunique()),
                        "period": [str(tasks.creation_time.min()), str(tasks.creation_time.max())],
                        "location_source": tasks.location_source.value_counts().to_dict(),
                        "runtime_sec": round(time.time() - t0, 3)},
            "join_validation": joins,
            "kpis": kp,
            "dispatch_summary": format_dispatches(D),
        }
        if include_execution_log:
            body["execution_log"] = format_log(L)
        return clean(body)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ════════════════════════════════════════════════════════════════════════════
# UTILITY
# ════════════════════════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/v1/config/defaults", summary="All engine defaults (every value is an assumption)")
def config_defaults():
    return dataclasses.asdict(eng.Config())