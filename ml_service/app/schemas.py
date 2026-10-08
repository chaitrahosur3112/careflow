from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class WaitTimeRequest(BaseModel):
    department_id: str
    current_queue_length: int = Field(ge=0)
    triage_level: Literal["P1", "P2", "P3"]
    staff_on_duty: int = Field(ge=0)
    time_of_day: int = Field(ge=0, le=23)
    day_of_week: int = Field(ge=0, le=6)


class WaitTimeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    department_id: str
    predicted_wait_minutes: float
    model_version: str


class OvercrowdingRiskRequest(BaseModel):
    department_id: str
    admission_rate_last_1h: float = Field(ge=0)
    bed_occupancy_pct: float = Field(ge=0, le=100)
    hour_of_day: int = Field(ge=0, le=23)


class OvercrowdingRiskResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    department_id: str
    risk_score: float
    severity: Literal["low", "amber", "red"]
    model_version: str


class StaffingRecommendationRequest(BaseModel):
    department_id: str
    current_load: float = Field(
        ge=0, description="Current patient queue length (count of patients waiting), not a percentage."
    )
    staff_on_duty: int = Field(ge=0)
    predicted_risk: float = Field(ge=0, le=100)


class StaffingRecommendationResponse(BaseModel):
    department_id: str
    recommendation: str


class MetricBlock(BaseModel):
    mae: float
    rmse: float
    r2: float
    test_samples: int


class ModelMetricsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    wait_time: Optional[MetricBlock]
    overcrowding_risk: Optional[MetricBlock]
    model_version: str
