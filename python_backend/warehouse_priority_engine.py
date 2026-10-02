#!/usr/bin/env python3
"""
Dynamic Urgency-Aware Picking Priority Engine  (V1 - scheduler, not ML)
======================================================================

Pipeline
--------
Customer_Order.csv ─┐
Picking_Wave.csv  ──┼─► JOIN ─► normalized TASK TABLE ─► PRIORITY ENGINE ─► pick next task
Product.csv       ──┤            (stage 1)                (slack tiers +      │
Storage_Location  ──┤                                      weighted score)   ▼
Support_Points    ──┘                                              update warehouse state
                                                                           │
                                         dispatch requirement met? ── NO ──┘ (recalculate)
                                                    │ YES
                                                    ▼
                                              DISPATCH READY

Usage
-----
    python warehouse_priority_engine.py --selftest
    python warehouse_priority_engine.py --data Order_Picking_Dataset...zip --max-waves 300
    python warehouse_priority_engine.py --data <zip-or-folder> --compare --max-waves 500
    python warehouse_priority_engine.py --data <zip-or-folder> --start 2023-03-01 --end 2023-03-08

ASSUMPTIONS (not measured ground truth - all configurable in `Config`)
---------------------------------------------------------------------
* The dataset has no dispatch cutoff  -> deadline = creation_time + SIMULATED_DISPATCH_SLA_MINUTES.
* Picker speed, unit pick time and the coordinate unit are assumptions.
* One dispatch = one picking wave (all orders in a wave share one creation timestamp).
* Each operator in the data is one picker; operators work continuously (no shifts/breaks).
* Z in Storage_Location is a *floor* index; Z_WEIGHT lets you price a floor change.
"""
from __future__ import annotations

import argparse
import heapq
import io
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

TIER_NAMES = ["CRITICAL", "URGENT", "HIGH", "NORMAL"]


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION  (every number below is an assumption, not a measurement)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class Config:
    # --- deadlines -----------------------------------------------------------
    SIMULATED_DISPATCH_SLA_MINUTES: float = 90.0   # deadline = creation + SLA
    # --- picker model --------------------------------------------------------
    PICKER_SPEED_MPS: float = 1.2                  # assumption
    UNIT_PICK_TIME_SEC: float = 5.0                # assumption
    COORD_UNIT_TO_METERS: float = 1.0              # README says metres; use 0.1 if x/y are really decimetres
    Z_WEIGHT: float = 1.0                          # cost of |dz| (floor change) relative to x/y units
    DEPOT_LOCATION: str = "RC-01"                  # picker start + fallback for unmapped locations
    # --- priority tiers (minutes of slack) -----------------------------------
    TIER_URGENT_MAX_SLACK_MIN: float = 15.0
    TIER_HIGH_MAX_SLACK_MIN: float = 30.0
    # --- score weights (configuration, NOT mathematically optimal) -----------
    W_URGENCY: float = 0.40
    W_QUANTITY: float = 0.25
    W_COMPLEXITY: float = 0.20
    W_DISTANCE: float = 0.15
    SLACK_HORIZON_MIN: float | None = None         # "MaxSlack" for urgency; default = SLA

    @property
    def horizon_min(self) -> float:
        return self.SLACK_HORIZON_MIN or self.SIMULATED_DISPATCH_SLA_MINUTES


# ════════════════════════════════════════════════════════════════════════════
# STAGE 0 - LOAD RAW CSVs (from a folder or straight from the .zip)
# ════════════════════════════════════════════════════════════════════════════
def _read(source: str | Path, name: str, sep: str) -> pd.DataFrame:
    source = Path(source)
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z:
            member = next(m for m in z.namelist() if m.split("/")[-1] == name)
            buf = io.BytesIO(z.read(member))
    else:
        buf = source / name
    df = pd.read_csv(buf, sep=sep, dtype=str, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    for c in df.columns:                      # the dataset pads cells with spaces
        df[c] = df[c].str.strip()
    return df


def load_raw(source: str | Path) -> dict[str, pd.DataFrame]:
    return {
        "orders": _read(source, "Customer_Order.csv", ";"),
        "waves": _read(source, "Picking_Wave.csv", ";"),
        "products": _read(source, "Product.csv", ";"),
        "storage": _read(source, "Storage_Location.csv", ","),   # NB: comma-delimited
        "support": _read(source, "Support_Points_Navigation.csv", ";"),
    }


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 - CLEAN + JOIN  ->  NORMALIZED TASK TABLE
# ════════════════════════════════════════════════════════════════════════════
def _normalize_order_size(s: pd.Series) -> pd.Series:
    """Customer_Order lost the decimal point (95 -> 9.5, 35 -> 3.5); Picking_Wave kept it.
    Real sizes are 1-16 or 215-305, so anything in [20,130] is a x10 value."""
    v = pd.to_numeric(s, errors="coerce")
    return v.where(~v.between(20, 130), v / 10.0)


def _prep_orders(co: pd.DataFrame) -> pd.DataFrame:
    co = co.copy()
    co["creation_time"] = pd.to_datetime(co["creationDate"], format="%d/%m/%Y %H:%M")
    co["qty"] = co["quantity (units)"].astype(int)
    co["size"] = _normalize_order_size(co["Size (US)"])
    return co


def _prep_waves(pw: pd.DataFrame) -> pd.DataFrame:
    pw = pw.copy()
    pw["size"] = pw["Size (US)"].astype(float)
    pw["qty"] = pw["quantityToPick (units)"].astype(int)
    pw["_seq"] = np.arange(len(pw))           # original pick-list order
    return pw


def _location_lookup(raw: dict, cfg: Config) -> pd.DataFrame:
    st = raw["storage"][["originalLocation", "x", "y", "z"]].copy()
    st.columns = ["location", "x", "y", "z"]
    st[["x", "y", "z"]] = st[["x", "y", "z"]].astype(float)
    st["location_source"] = "storage_location"

    sp = raw["support"].copy()
    nums = sp["points_specified"].str.findall(r"-?\d+(?:\.\d+)?")
    sp = pd.DataFrame({"location": sp["labels"], "x": nums.str[0].astype(float),
                       "y": nums.str[1].astype(float), "z": nums.str[2].astype(float),
                       "location_source": "support_point"})
    # Support_Points_Navigation only lists RC-08..RC-17, but Picking_Wave uses RC-01..RC-05 heavily
    # (RC-01 alone = ~11% of picks). LC/CC/RC share the same y per index (RC-08 and LC-08 are both
    # y=631), so infer RC-nn = (RC column x, LC-nn y, z) and flag it as inferred.
    have = set(sp["location"])
    rc_x = sp.loc[sp.location.str.startswith("RC-"), "x"].median()
    inferred = []
    for _, r in sp[sp.location.str.startswith("LC-")].iterrows():
        rc = "RC-" + r.location[3:]
        if rc not in have:
            inferred.append({"location": rc, "x": rc_x, "y": r.y, "z": r.z,
                             "location_source": "support_point_inferred"})
    lk = pd.concat([st, sp, pd.DataFrame(inferred)]).drop_duplicates("location", keep="first")
    if cfg.DEPOT_LOCATION not in set(lk["location"]):
        raise ValueError(f"DEPOT_LOCATION {cfg.DEPOT_LOCATION!r} not found in location tables")
    return lk


def validate_joins(raw: dict, cfg: Config) -> dict:
    """Join-integrity report across the four source tables (run on the FULL data)."""
    co, pw = _prep_orders(raw["orders"]), _prep_waves(raw["waves"])
    lk = _location_lookup(raw, cfg)
    a = co.groupby(["waveNumber", "Reference", "size"]).qty.sum().rename("order_qty")
    b = pw.groupby(["waveNumber", "reference", "size"]).qty.sum().rename("pick_qty")
    b.index.names = a.index.names
    m = pd.concat([a, b], axis=1)
    src = pw["locations"].map(lk.set_index("location")["location_source"]).fillna("UNMAPPED")
    return {
        "order_rows": len(co), "pick_rows": len(pw),
        "waves_in_orders": co.waveNumber.nunique(), "waves_in_picking": pw.waveNumber.nunique(),
        "waves_without_pick_rows": len(set(co.waveNumber) - set(pw.waveNumber)),
        "waves_with_>1_creation_time": int((co.groupby("waveNumber").creation_time.nunique() > 1).sum()),
        "waves_with_>1_operator": int((pw.groupby("waveNumber").operator.nunique() > 1).sum()),
        "pick_lines_without_order_line": int(m.order_qty.isna().sum()),
        "order_lines_without_pick_rows": int(m.pick_qty.isna().sum()),
        "order_units_without_pick_rows": int(m.loc[m.pick_qty.isna(), "order_qty"].sum()),
        "line_quantity_mismatches": int(((m.order_qty != m.pick_qty) & m.order_qty.notna() & m.pick_qty.notna()).sum()),
        "pick_refs_missing_in_product": int((~pw.reference.isin(raw["products"].Reference)).sum()),
        "pick_units_by_location_source": src.value_counts().to_dict(),
    }


def build_task_table(raw: dict, cfg: Config, max_waves: int | None = None,
                     start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """One row per (wave, reference, size, location, operator) pick task."""
    co, pw = _prep_orders(raw["orders"]), _prep_waves(raw["waves"])
    lk = _location_lookup(raw, cfg)

    # wave -> creation time (Customer_Order)
    wave_info = co.groupby("waveNumber").agg(creation_time=("creation_time", "min"),
                                             n_orders=("orderNumber", "nunique")).reset_index()

    # Picking_Wave is one row per unit -> aggregate to tasks
    tasks = (pw.groupby(["waveNumber", "reference", "size", "locations", "operator"], sort=False)
               .agg(quantity_required=("qty", "sum"), pick_seq=("_seq", "min")).reset_index())
    tasks = tasks.merge(wave_info, on="waveNumber", how="inner")           # drops waves with no order record
    tasks = tasks.merge(raw["products"][["Reference", "ABCCOD"]].rename(
        columns={"Reference": "reference", "ABCCOD": "abc_class"}), on="reference", how="left")

    # optional subsetting (chronological, whole waves only)
    if start:
        tasks = tasks[tasks.creation_time >= pd.Timestamp(start)]
    if end:
        tasks = tasks[tasks.creation_time < pd.Timestamp(end)]
    if max_waves:
        order = (tasks[["waveNumber", "creation_time"]].drop_duplicates()
                 .sort_values(["creation_time", "waveNumber"]).head(max_waves).waveNumber)
        tasks = tasks[tasks.waveNumber.isin(order)]

    # location -> x,y,z  (storage -> support point -> depot fallback)
    tasks = tasks.merge(lk, left_on="locations", right_on="location", how="left")
    depot = lk[lk.location == cfg.DEPOT_LOCATION].iloc[0]
    miss = tasks["x"].isna()
    tasks.loc[miss, ["x", "y", "z"]] = depot[["x", "y", "z"]].values
    tasks.loc[miss, "location_source"] = "fallback_depot"
    tasks["location"] = tasks["locations"]

    tasks = tasks.sort_values(["creation_time", "waveNumber", "pick_seq"]).reset_index(drop=True)
    tasks["task_id"] = ["T%07d" % i for i in range(1, len(tasks) + 1)]
    tasks["wave_number"] = tasks["waveNumber"]
    tasks["dispatch_id"] = "D" + tasks["waveNumber"].astype(str)
    tasks["quantity_picked"] = 0
    tasks["remaining_quantity"] = tasks["quantity_required"] - tasks["quantity_picked"]
    tasks["dispatch_deadline"] = tasks["creation_time"] + pd.Timedelta(minutes=cfg.SIMULATED_DISPATCH_SLA_MINUTES)
    tasks["estimated_pick_time_sec"] = tasks["remaining_quantity"] * cfg.UNIT_PICK_TIME_SEC
    cols = ["task_id", "dispatch_id", "wave_number", "reference", "size", "quantity_required",
            "quantity_picked", "remaining_quantity", "location", "location_source", "x", "y", "z",
            "operator", "creation_time", "abc_class", "n_orders", "dispatch_deadline",
            "estimated_pick_time_sec", "pick_seq"]
    return tasks[cols]


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 - PRIORITY ENGINE  (slack -> tier -> score)
# ════════════════════════════════════════════════════════════════════════════
@dataclass
class Evaluation:
    travel_m: np.ndarray
    travel_s: np.ndarray
    pick_s: np.ndarray
    total_s: np.ndarray
    slack_min: np.ndarray
    tier: np.ndarray        # 0 CRITICAL .. 3 NORMAL
    score: np.ndarray       # 0..1, only comparable inside one tier / one decision


class PriorityEngine:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    # --- complexity: distinct open locations still needed by the task's dispatch ---------
    @staticmethod
    def n_locations_per_dispatch(dispatch_code: np.ndarray, loc_code: np.ndarray) -> np.ndarray:
        M = int(loc_code.max()) + 1
        uk = np.unique(dispatch_code.astype(np.int64) * M + loc_code)
        ud, cnt = np.unique(uk // M, return_counts=True)
        return cnt[np.searchsorted(ud, dispatch_code)]

    def evaluate(self, now_s, pos, deadline_s, remaining, x, y, z, dispatch_code, loc_code) -> Evaluation:
        c = self.cfg
        px, py, pz = pos
        # Manhattan distance (x,y) + weighted floor change
        dist = (np.abs(x - px) + np.abs(y - py) + c.Z_WEIGHT * np.abs(z - pz)) * c.COORD_UNIT_TO_METERS
        travel_s = dist / c.PICKER_SPEED_MPS
        pick_s = remaining * c.UNIT_PICK_TIME_SEC
        total_s = pick_s + travel_s
        slack = (deadline_s - now_s - total_s) / 60.0                 # minutes

        tier = np.where(slack <= 0, 0,
               np.where(slack <= c.TIER_URGENT_MAX_SLACK_MIN, 1,
               np.where(slack <= c.TIER_HIGH_MAX_SLACK_MIN, 2, 3)))

        eps = 1e-9
        U = np.clip(1.0 - slack / c.horizon_min, 0.0, 1.0)
        Q = remaining / max(float(np.max(remaining)), eps)
        nloc = self.n_locations_per_dispatch(dispatch_code, loc_code)
        C = nloc / max(float(nloc.max()), eps)
        D = dist / max(float(dist.max()), eps)
        score = c.W_URGENCY * U + c.W_QUANTITY * Q + c.W_COMPLEXITY * C + c.W_DISTANCE * D
        return Evaluation(dist, travel_s, pick_s, total_s, slack, tier, score)

    @staticmethod
    def select(ev: Evaluation, tiebreak: np.ndarray) -> int:
        """Lowest tier first, then highest score, then lowest tiebreak id."""
        return int(np.lexsort((tiebreak, -ev.score, ev.tier))[0])


def snapshot_priorities(tasks: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Initial priority view: each task evaluated at its order-creation time, picker at depot."""
    lk_depot = tasks.attrs.get("depot")  # set by caller; fallback below
    t0 = tasks.creation_time.min()
    now = (tasks.creation_time - t0).dt.total_seconds().values
    dl = (tasks.dispatch_deadline - t0).dt.total_seconds().values
    depot = lk_depot if lk_depot is not None else (0.0, 0.0, 1.0)
    d_code = pd.factorize(tasks.dispatch_id)[0]
    l_code = pd.factorize(tasks.location)[0]
    ev = PriorityEngine(cfg).evaluate(now, depot, dl, tasks.remaining_quantity.values.astype(float),
                                      tasks.x.values, tasks.y.values, tasks.z.values, d_code, l_code)
    out = tasks.copy()
    out["travel_distance_m"] = ev.travel_m
    out["estimated_total_time_min"] = ev.total_s / 60
    out["slack_min"] = ev.slack_min
    out["priority_level"] = [TIER_NAMES[i] for i in ev.tier]
    out["priority_score"] = ev.score
    return out


# ════════════════════════════════════════════════════════════════════════════
# STAGE 3 - DISPATCH REQUIREMENT LAYER
# ════════════════════════════════════════════════════════════════════════════
class DispatchTracker:
    """dispatch D1: {(ref,size): required}, progress {(ref,size): picked}  ->  ready when all met."""

    def __init__(self, tasks: pd.DataFrame):
        self.deadline, self.creation = {}, {}
        self.required: dict[str, dict] = {}
        self.picked: dict[str, dict] = {}
        for did, g in tasks.groupby("dispatch_id", sort=False):
            req = g.groupby(["reference", "size"]).quantity_required.sum()
            self.required[did] = req.to_dict()
            self.picked[did] = {k: 0 for k in self.required[did]}
            self.deadline[did] = g.dispatch_deadline.iloc[0]
            self.creation[did] = g.creation_time.iloc[0]
        self.ready_at: dict[str, float] = {}
        self._open = {d: sum(r.values()) for d, r in self.required.items()}

    def record_pick(self, did: str, ref: str, size: float, qty: int, t_end_s: float):
        self.picked[did][(ref, size)] += qty
        self._open[did] -= qty
        if self._open[did] == 0:
            self.ready_at[did] = max(self.ready_at.get(did, 0.0), t_end_s)

    def remaining(self, did: str) -> dict:
        return {k: self.required[did][k] - v for k, v in self.picked[did].items()
                if self.required[did][k] - v > 0}

    def is_ready(self, did: str) -> bool:
        return self._open[did] == 0


# ════════════════════════════════════════════════════════════════════════════
# STAGE 4 - DYNAMIC SIMULATION LOOP
# ════════════════════════════════════════════════════════════════════════════
def simulate(tasks: pd.DataFrame, cfg: Config, policy: str = "priority", depot_xyz=(0.0, 0.0, 1.0)):
    """Discrete-event simulation. Every operator is a picker; at each moment a picker becomes free
    we re-admit newly arrived tasks, recompute slack/tier/score for ALL its open tasks from the
    current clock + picker position, pick the winner, update state, repeat.
    policy: 'priority' (this engine) | 'fifo' | 'nearest'  (baselines for comparison)."""
    engine = PriorityEngine(cfg)
    t0 = tasks.creation_time.min()
    n = len(tasks)
    creation = (tasks.creation_time - t0).dt.total_seconds().values
    deadline = (tasks.dispatch_deadline - t0).dt.total_seconds().values
    x, y, z = tasks.x.values, tasks.y.values, tasks.z.values
    qty_req = tasks.quantity_required.values.astype(float)
    remaining = tasks.remaining_quantity.values.astype(float).copy()
    picked = tasks.quantity_picked.values.astype(float).copy()
    d_code = pd.factorize(tasks.dispatch_id)[0]
    l_code = pd.factorize(tasks.location)[0]
    refs, sizes = tasks.reference.values, tasks.size.values
    dids, task_ids = tasks.dispatch_id.values, tasks.task_id.values
    op_names, op_code = np.unique(tasks.operator.values, return_inverse=True)

    tracker = DispatchTracker(tasks)
    # tasks are already sorted by (creation, wave, seq) -> per-operator index lists keep that order
    queues = [np.flatnonzero(op_code == o) for o in range(len(op_names))]
    ptr = [0] * len(op_names)
    active = [np.empty(len(q), dtype=np.int64) for q in queues]
    n_act = [0] * len(op_names)
    pos = [depot_xyz] * len(op_names)
    heap = [(creation[q[0]], o) for o, q in enumerate(queues) if len(q)]
    heapq.heapify(heap)

    log = []
    while heap:
        now, o = heapq.heappop(heap)
        q, a_buf = queues[o], active[o]
        # new orders arrive -> admit
        while ptr[o] < len(q) and creation[q[ptr[o]]] <= now:
            a_buf[n_act[o]] = q[ptr[o]]; n_act[o] += 1; ptr[o] += 1
        if n_act[o] == 0:
            if ptr[o] < len(q):
                heapq.heappush(heap, (creation[q[ptr[o]]], o))
            continue

        a = a_buf[:n_act[o]]
        ev = engine.evaluate(now, pos[o], deadline[a], remaining[a], x[a], y[a], z[a], d_code[a], l_code[a])
        if policy == "priority":
            k = engine.select(ev, a)
        elif policy == "fifo":
            k = int(np.argmin(a))                       # a = global index = (creation, wave, seq) order
        elif policy == "nearest":
            k = int(np.lexsort((a, ev.travel_m))[0])
        else:
            raise ValueError(policy)

        i = int(a[k])
        qty = remaining[i]
        end = now + ev.travel_s[k] + ev.pick_s[k]
        log.append((task_ids[i], op_names[o], now, ev.travel_m[k], ev.travel_s[k], ev.pick_s[k], end,
                    TIER_NAMES[ev.tier[k]], ev.score[k], ev.slack_min[k], n_act[o]))

        # execute + update warehouse state
        picked[i] += qty; remaining[i] = 0.0
        tracker.record_pick(dids[i], refs[i], sizes[i], int(qty), end)
        pos[o] = (x[i], y[i], z[i])
        a_buf[k] = a_buf[n_act[o] - 1]; n_act[o] -= 1      # swap-remove (task complete)
        heapq.heappush(heap, (end, o))

    # ---- results --------------------------------------------------------------------------
    to_dt = lambda s: t0 + pd.to_timedelta(s, unit="s")
    L = pd.DataFrame(log, columns=["task_id", "operator", "start_s", "travel_m", "travel_s", "pick_s",
                                   "end_s", "tier_at_pick", "score_at_pick", "slack_min_at_pick", "open_tasks"])
    L["start_time"], L["end_time"] = to_dt(L.start_s), to_dt(L.end_s)

    rows = []
    for did in tracker.required:
        ready = to_dt(tracker.ready_at[did]) if did in tracker.ready_at else pd.NaT
        rows.append((did, tracker.creation[did], tracker.deadline[did], ready,
                     sum(tracker.required[did].values()), len(tracker.required[did])))
    D = pd.DataFrame(rows, columns=["dispatch_id", "creation_time", "deadline", "ready_time",
                                    "units_required", "distinct_items"])
    D["lateness_min"] = ((D.ready_time - D.deadline).dt.total_seconds() / 60).clip(lower=0)
    D["on_time"] = D.ready_time <= D.deadline
    D["flow_time_min"] = (D.ready_time - D.creation_time).dt.total_seconds() / 60
    return L, D, dict(remaining=remaining, picked=picked, qty_req=qty_req, tracker=tracker)


def verify_simulation(tasks, L, D, state) -> None:
    """Hard conservation checks - these must hold for any correct run."""
    assert len(L) == len(tasks) and L.task_id.is_unique, "every task must be executed exactly once"
    assert (state["remaining"] == 0).all(), "no task may keep remaining quantity"
    assert np.allclose(state["picked"], state["qty_req"]), "picked must equal required"
    assert D.ready_time.notna().all() and all(state["tracker"].is_ready(d) for d in D.dispatch_id), \
        "all dispatches must be ready"
    assert (L.end_s >= L.start_s).all()
    for _, g in L.groupby("operator"):                       # one operator cannot do two things at once
        assert (g.sort_values("start_s").start_s.values[1:] >= g.sort_values("start_s").end_s.values[:-1] - 1e-6).all()
    assert (L.merge(tasks[["task_id", "creation_time"]], on="task_id").eval("start_time >= creation_time")).all(), \
        "no task may start before its order exists"


def kpis(L: pd.DataFrame, D: pd.DataFrame) -> dict:
    late = D.lateness_min[D.lateness_min > 0]
    return {
        "dispatches": len(D),
        "on_time_%": round(100 * D.on_time.mean(), 1),
        "mean_lateness_min (late only)": round(late.mean(), 1) if len(late) else 0.0,
        "p95_lateness_min (all)": round(D.lateness_min.quantile(0.95), 1),
        "max_lateness_min": round(D.lateness_min.max(), 1),
        "mean_flow_time_min": round(D.flow_time_min.mean(), 1),
        "total_travel_km": round(L.travel_m.sum() / 1000, 1),
        "picks_at_CRITICAL_%": round(100 * (L.tier_at_pick == "CRITICAL").mean(), 1),
    }


# ════════════════════════════════════════════════════════════════════════════
# SELF-TESTS (the worked examples from the design doc + tier-ordering guarantee)
# ════════════════════════════════════════════════════════════════════════════
def selftest() -> None:
    cfg = Config(COORD_UNIT_TO_METERS=1.0)
    eng = PriorityEngine(cfg)
    zero = (0.0, 0.0, 1.0)
    one = lambda v: np.array([v], dtype=float)

    def run(now_min, deadline_min, task_min):
        rem = task_min * 60 / cfg.UNIT_PICK_TIME_SEC           # zero-travel task of that duration
        return eng.evaluate(now_min * 60, zero, one(deadline_min * 60), one(rem), one(0), one(0), one(1),
                            np.array([0]), np.array([0]))
    e = run(0, 30, 10);  assert abs(e.slack_min[0] - 20) < 1e-9 and e.tier[0] == 2    # 08:00/08:30/10min -> 20, HIGH
    e = run(0, 15, 12);  assert abs(e.slack_min[0] - 3) < 1e-9 and e.tier[0] == 1     # 08:00/08:15/12min -> 3, URGENT
    assert run(0, 10, 10).tier[0] == 0 and run(0, 5, 10).tier[0] == 0                  # slack <= 0 -> CRITICAL
    assert run(0, 25, 10).tier[0] == 1 and run(0, 40, 10).tier[0] == 2 and run(0, 41, 10).tier[0] == 3
    # Manhattan distance and speed
    e = eng.evaluate(0, (0, 0, 1), one(1e9), one(1), one(3), one(4), one(2), np.array([0]), np.array([0]))
    assert e.travel_m[0] == 3 + 4 + 1 and abs(e.travel_s[0] - 8 / 1.2) < 1e-9
    # Tier beats proximity: far CRITICAL task must be chosen over a near NORMAL one
    e = eng.evaluate(0, zero, np.array([100.0, 1e6]), np.array([10.0, 1.0]), np.array([500.0, 1.0]),
                     np.array([500.0, 0.0]), np.array([1.0, 1.0]), np.array([0, 1]), np.array([0, 1]))
    assert e.tier[0] == 0 and e.tier[1] == 3 and eng.select(e, np.array([0, 1])) == 0
    print("selftest: all assertions passed")


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", help="dataset .zip or folder with the CSVs")
    p.add_argument("--out", default="engine_output", help="output folder")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--policy", default="priority", choices=["priority", "fifo", "nearest"])
    p.add_argument("--compare", action="store_true", help="run priority vs fifo vs nearest baselines")
    p.add_argument("--max-waves", type=int, help="use only the first N waves chronologically")
    p.add_argument("--start", help="YYYY-MM-DD (inclusive)")
    p.add_argument("--end", help="YYYY-MM-DD (exclusive)")
    p.add_argument("--sla", type=float, help="dispatch SLA minutes (default 90)")
    p.add_argument("--speed", type=float, help="picker speed m/s (default 1.2)")
    p.add_argument("--unit-pick-sec", type=float, help="seconds per unit (default 5)")
    p.add_argument("--coord-scale", type=float, help="metres per coordinate unit (default 1.0)")
    p.add_argument("--weights", type=float, nargs=4, metavar=("U", "Q", "C", "D"))
    args = p.parse_args(argv)

    if args.selftest:
        selftest()
        if not args.data:
            return 0
    if not args.data:
        p.error("--data is required")

    cfg = Config()
    if args.sla: cfg.SIMULATED_DISPATCH_SLA_MINUTES = args.sla
    if args.speed: cfg.PICKER_SPEED_MPS = args.speed
    if args.unit_pick_sec: cfg.UNIT_PICK_TIME_SEC = args.unit_pick_sec
    if args.coord_scale: cfg.COORD_UNIT_TO_METERS = args.coord_scale
    if args.weights: cfg.W_URGENCY, cfg.W_QUANTITY, cfg.W_COMPLEXITY, cfg.W_DISTANCE = args.weights

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    print("Loading raw data ...")
    raw = load_raw(args.data)

    print("\n== Join validation (full dataset) ==")
    for k, v in validate_joins(raw, cfg).items():
        print(f"  {k:36s} {v}")

    tasks = build_task_table(raw, cfg, args.max_waves, args.start, args.end)
    lk = _location_lookup(raw, cfg)
    depot = tuple(lk[lk.location == cfg.DEPOT_LOCATION].iloc[0][["x", "y", "z"]].astype(float))
    tasks.attrs["depot"] = depot
    print(f"\n== Task table ==\n  tasks={len(tasks):,}  dispatches={tasks.dispatch_id.nunique():,}  "
          f"units={tasks.quantity_required.sum():,}  operators={tasks.operator.nunique()}  "
          f"period={tasks.creation_time.min()} -> {tasks.creation_time.max()}")
    print("  location_source:", tasks.location_source.value_counts().to_dict())
    print("  abc_class      :", tasks.abc_class.value_counts().to_dict())

    snap = snapshot_priorities(tasks, cfg)
    snap.to_csv(out / "task_table.csv", index=False)
    print("  initial priority levels (at order creation, picker at depot):",
          snap.priority_level.value_counts().to_dict())

    policies = ["priority", "fifo", "nearest"] if args.compare else [args.policy]
    results = {}
    for pol in policies:
        t = time.time()
        L, D, state = simulate(tasks, cfg, pol, depot)
        verify_simulation(tasks, L, D, state)
        results[pol] = kpis(L, D)
        print(f"\n[{pol}] simulated {len(L):,} picks in {time.time() - t:.1f}s - conservation checks passed")
        if pol == policies[0]:
            L.to_csv(out / f"execution_log_{pol}.csv", index=False)
            D.to_csv(out / f"dispatch_summary_{pol}.csv", index=False)

    print("\n== KPIs ==")
    print(pd.DataFrame(results).to_string())
    print(f"\nFiles written to {out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())