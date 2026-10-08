import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.ml.staffing import recommend_staffing
from app.schemas import (
    ModelMetricsResponse,
    OvercrowdingRiskRequest,
    OvercrowdingRiskResponse,
    StaffingRecommendationRequest,
    StaffingRecommendationResponse,
    WaitTimeRequest,
    WaitTimeResponse,
)

router = APIRouter()

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"


@router.post("/predict/wait-time", response_model=WaitTimeResponse)
def predict_wait_time(payload: WaitTimeRequest, request: Request):
    model = request.app.state.wait_time_model
    predicted = model.predict(
        current_queue_length=payload.current_queue_length,
        staff_on_duty=payload.staff_on_duty,
        time_of_day=payload.time_of_day,
        day_of_week=payload.day_of_week,
        triage_level=payload.triage_level,
    )
    return WaitTimeResponse(
        department_id=payload.department_id,
        predicted_wait_minutes=predicted,
        model_version=model.version,
    )


@router.post("/predict/overcrowding-risk", response_model=OvercrowdingRiskResponse)
def predict_overcrowding_risk(payload: OvercrowdingRiskRequest, request: Request):
    model = request.app.state.overcrowding_model
    risk_score, severity = model.predict(
        admission_rate_last_1h=payload.admission_rate_last_1h,
        bed_occupancy_pct=payload.bed_occupancy_pct,
        hour_of_day=payload.hour_of_day,
    )
    return OvercrowdingRiskResponse(
        department_id=payload.department_id,
        risk_score=risk_score,
        severity=severity,
        model_version=model.version,
    )


@router.post("/recommend/staffing", response_model=StaffingRecommendationResponse)
def recommend_staffing_endpoint(payload: StaffingRecommendationRequest):
    text = recommend_staffing(
        current_load=payload.current_load,
        staff_on_duty=payload.staff_on_duty,
        predicted_risk=payload.predicted_risk,
    )
    return StaffingRecommendationResponse(department_id=payload.department_id, recommendation=text)


@router.get("/model/metrics", response_model=ModelMetricsResponse)
def model_metrics():
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=503, detail="Metrics not found — run train.py first.")
    with open(metrics_path) as f:
        data = json.load(f)
    return ModelMetricsResponse(**data)
