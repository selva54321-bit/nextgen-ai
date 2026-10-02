from typing import Optional, List
from pydantic import BaseModel


class Dimensions(BaseModel):
    depth_cm: float
    width_cm: float
    height_cm: float


class TimeWindow(BaseModel):
    start_time_utc: Optional[str] = None
    end_time_utc: Optional[str] = None


class Package(BaseModel):
    dimensions: Dimensions
    planned_service_time_seconds: float = 0
    time_window: Optional[TimeWindow] = None


class RouteInput(BaseModel):
    station_code: str
    date: str
    executor_capacity_cm3: float
    stops: int
    route_num_packages: int


class StopInput(BaseModel):
    zone_id: str
    packages: List[Package]


class PredictionRequest(BaseModel):
    route: RouteInput
    stop: StopInput


class Factor(BaseModel):
    factor: str
    impact: str
    description: str
    impact: str
    contribution: float



class PredictionResponse(BaseModel):
    failure_probability: float
    risk_band: str
    top_factors: List[Factor]