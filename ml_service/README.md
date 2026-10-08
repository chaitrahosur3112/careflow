# CareFlow ML Service (Phase 2)

FastAPI microservice serving two models trained on fully synthetic data:

- **Wait-time prediction** — Gradient Boosting Regressor.
  Inputs: `department_id, current_queue_length, triage_level, staff_on_duty, time_of_day, day_of_week`
  MAE ≈ 3.4 min, R² ≈ 0.99 on held-out synthetic test data.
- **Overcrowding risk** — Gradient Boosting Regressor trained on
  Holt-Winters-smoothed 2-hour-ahead occupancy forecasts (statsmodels),
  blended with live bed occupancy so an already-critical department is
  never masked by the forecast. Returns a 0–100 score + `low`/`amber`/`red`.
- **Staffing recommendation** — rule-based, not ML (deliberately
  explainable): composes a plain-English recommendation from current
  load, staff on duty, and the predicted risk score.

No real hospital data is used anywhere — see `data_generator.py`.

## Setup

```bash
cd ml_service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python train.py          # trains both models, saves artifacts/*.pkl + metrics.json
uvicorn app.main:app --reload --port 8001
```

Visit `http://localhost:8001/docs` for interactive Swagger UI.

## Endpoints

| Method | Path | Auth |
|---|---|---|
| POST | `/predict/wait-time` | none (internal service — called by Django, not exposed publicly) |
| POST | `/predict/overcrowding-risk` | none |
| POST | `/recommend/staffing` | none |
| GET | `/model/metrics` | none |
| GET | `/health` | none |

This service has no auth of its own by design — it's meant to sit
behind the Django backend on a private network/Docker network and never
be exposed directly to the internet. CORS is locked to the Django
backend's origin only (see `.env.example`).

## Retraining

Re-run `python train.py` any time — it regenerates fresh synthetic data,
retrains both models, and overwrites `artifacts/*.pkl` and
`artifacts/metrics.json`. The Django backend's `/analytics/model-accuracy`
endpoint separately tracks predicted-vs-actual accuracy on live traffic
over time (a different, complementary metric from this file's offline
test-set metrics).

## Why statsmodels instead of Prophet

The spec allows either. Prophet pulls in a Stan backend that's slow to
install and overkill for an academic demo; statsmodels' Holt-Winters
exponential smoothing gives the same seasonal-trend decomposition
CareFlow needs (daily occupancy cycles) with a much lighter dependency
footprint — worth mentioning if asked in viva.
