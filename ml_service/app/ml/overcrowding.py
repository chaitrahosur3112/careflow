from pathlib import Path

import joblib
import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"

AMBER_THRESHOLD = 80
RED_THRESHOLD = 95


class OvercrowdingModel:
    def __init__(self):
        path = ARTIFACTS_DIR / "overcrowding_model.pkl"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found — run `python train.py` in ml_service/ before starting the API."
            )
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.feature_order = bundle["feature_order"]
        self.version = bundle["version"]

    def predict(self, admission_rate_last_1h, bed_occupancy_pct, hour_of_day):
        X = np.array([[admission_rate_last_1h, bed_occupancy_pct, hour_of_day]])
        forecast_component = float(np.clip(self.model.predict(X)[0], 0, 100))

        # The trained model forecasts occupancy ~2h ahead and is a genuine
        # early-warning signal, but it should never be allowed to mask an
        # ALREADY-critical department: if current occupancy alone is at
        # crisis level, risk must reflect that immediately rather than
        # waiting on the forecast to catch up. Taking the max of "where
        # we are now" and "where the model thinks we're heading" gives
        # both the live safety net and the forward-looking warning.
        risk_score = round(max(forecast_component, bed_occupancy_pct), 1)

        if risk_score >= RED_THRESHOLD:
            severity = "red"
        elif risk_score >= AMBER_THRESHOLD:
            severity = "amber"
        else:
            severity = "low"

        return risk_score, severity
