from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"


class WaitTimeModel:
    def __init__(self):
        path = ARTIFACTS_DIR / "wait_time_model.pkl"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found — run `python train.py` in ml_service/ before starting the API."
            )
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.encoder = bundle["encoder"]
        self.feature_order = bundle["feature_order"]
        self.version = bundle["version"]

    def predict(self, current_queue_length, staff_on_duty, time_of_day, day_of_week, triage_level) -> float:
        triage_encoded = self.encoder.transform(
            pd.DataFrame([[triage_level]], columns=["triage_level"])
        )
        base_features = np.array([[current_queue_length, staff_on_duty, time_of_day, day_of_week]])
        X = np.hstack([base_features, triage_encoded])
        prediction = self.model.predict(X)[0]
        return round(max(0.0, float(prediction)), 1)
