import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    # TestClient must be used as a context manager for FastAPI's startup
    # event (which loads the trained models into app.state) to run.
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_metrics(client):
    response = client.get("/model/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "wait_time" in body
    assert "overcrowding_risk" in body


def test_wait_time_prediction(client):
    payload = {
        "department_id": "00000000-0000-0000-0000-000000000001",
        "current_queue_length": 8,
        "triage_level": "P2",
        "staff_on_duty": 4,
        "time_of_day": 14,
        "day_of_week": 2,
    }
    response = client.post("/predict/wait-time", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_wait_minutes"] >= 0


def test_overcrowding_risk_prediction(client):
    payload = {
        "department_id": "00000000-0000-0000-0000-000000000001",
        "admission_rate_last_1h": 12,
        "bed_occupancy_pct": 88,
        "hour_of_day": 14,
    }
    response = client.post("/predict/overcrowding-risk", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["severity"] in {"normal", "amber", "red"}


def test_staffing_recommendation_never_suggests_unrealistic_addition(client):
    """
    Regression test for the bug found during Phase 3 integration: a
    misread `current_load` unit could recommend adding a double-digit
    number of nurses in one call. current_load is a patient COUNT.
    """
    payload = {
        "department_id": "00000000-0000-0000-0000-000000000001",
        "current_load": 14,
        "staff_on_duty": 4,
        "predicted_risk": 82,
    }
    response = client.post("/recommend/staffing", json=payload)
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert "18 nurse" not in recommendation
