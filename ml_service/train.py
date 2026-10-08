"""
Trains CareFlow's two ML models on fully synthetic data and saves:
  artifacts/wait_time_model.pkl
  artifacts/overcrowding_model.pkl
  artifacts/metrics.json

Run this once before starting the API (`python train.py`), and re-run any
time you want to regenerate the models. No real hospital data is read or
required — see data_generator.py.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from data_generator import generate_occupancy_time_series, generate_wait_time_dataset

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

MODEL_VERSION = "v1"


def train_wait_time_model():
    print("Generating synthetic wait-time dataset...")
    df = generate_wait_time_dataset(n_rows=6000)

    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    triage_encoded = encoder.fit_transform(df[["triage_level"]])
    triage_cols = encoder.get_feature_names_out(["triage_level"])

    X = np.hstack(
        [
            df[["current_queue_length", "staff_on_duty", "time_of_day", "day_of_week"]].values,
            triage_encoded,
        ]
    )
    y = df["wait_minutes"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training GradientBoostingRegressor for wait-time prediction...")
    model = GradientBoostingRegressor(
        n_estimators=300, max_depth=3, learning_rate=0.05, random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "mae": round(mean_absolute_error(y_test, preds), 2),
        "rmse": round(mean_squared_error(y_test, preds) ** 0.5, 2),
        "r2": round(r2_score(y_test, preds), 3),
        "test_samples": len(y_test),
    }
    print(f"Wait-time model — MAE={metrics['mae']} min, RMSE={metrics['rmse']} min, R2={metrics['r2']}")

    joblib.dump(
        {"model": model, "encoder": encoder, "feature_order": ["current_queue_length", "staff_on_duty", "time_of_day", "day_of_week"], "triage_cols": list(triage_cols), "version": MODEL_VERSION},
        ARTIFACTS_DIR / "wait_time_model.pkl",
    )
    return metrics


def train_overcrowding_model():
    print("Generating synthetic occupancy time series...")
    series_df = generate_occupancy_time_series(n_departments=6, hours=24 * 60)

    # For each synthetic department, fit Holt-Winters exponential smoothing
    # to denoise the occupancy trajectory, then use the smoothed series to
    # build a "true" 2-hour-ahead occupancy label. This is the statsmodels
    # time-series component feeding the supervised model below.
    rows = []
    for dept_id, group in series_df.groupby("department_id"):
        group = group.sort_values("hour_index").reset_index(drop=True)
        fit = ExponentialSmoothing(
            group["bed_occupancy_pct"], trend="add", seasonal="add", seasonal_periods=24
        ).fit()
        smoothed = fit.fittedvalues.clip(0, 100)

        future_2h = smoothed.shift(-2)
        group = group.assign(smoothed_occupancy=smoothed, risk_label=future_2h.clip(0, 100))
        rows.append(group.dropna(subset=["risk_label"]))

    labeled = pd.concat(rows, ignore_index=True)

    X = labeled[["admission_rate_last_1h", "bed_occupancy_pct", "hour_of_day"]].values
    y = labeled["risk_label"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training GradientBoostingRegressor for overcrowding-risk prediction...")
    model = GradientBoostingRegressor(
        n_estimators=250, max_depth=3, learning_rate=0.05, random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        "mae": round(mean_absolute_error(y_test, preds), 2),
        "rmse": round(mean_squared_error(y_test, preds) ** 0.5, 2),
        "r2": round(r2_score(y_test, preds), 3),
        "test_samples": len(y_test),
    }
    print(f"Overcrowding-risk model — MAE={metrics['mae']}, RMSE={metrics['rmse']}, R2={metrics['r2']}")

    joblib.dump(
        {"model": model, "feature_order": ["admission_rate_last_1h", "bed_occupancy_pct", "hour_of_day"], "version": MODEL_VERSION},
        ARTIFACTS_DIR / "overcrowding_model.pkl",
    )
    return metrics


def main():
    wait_time_metrics = train_wait_time_model()
    overcrowding_metrics = train_overcrowding_model()

    metrics = {
        "wait_time": wait_time_metrics,
        "overcrowding_risk": overcrowding_metrics,
        "model_version": MODEL_VERSION,
    }
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved artifacts to {ARTIFACTS_DIR}/")


if __name__ == "__main__":
    main()
