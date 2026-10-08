"""
Synthetic data generators for CareFlow's two ML models.

Nothing here touches real hospital records — every value is simulated
from a plausible-but-invented formula plus random noise, purely so the
models have something realistic to learn from for the academic demo.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)

TRIAGE_BASE_MINUTES = {"P1": 5, "P2": 20, "P3": 45}
TRIAGE_QUEUE_SENSITIVITY = {"P1": 0.5, "P2": 1.5, "P3": 2.5}


def generate_wait_time_dataset(n_rows: int = 6000) -> pd.DataFrame:
    """
    Simulates ER wait-time observations.

    Ground-truth formula (used only to LABEL synthetic data, never seen
    by the model directly): wait time grows with queue length and falls
    with more staff on duty, with a triage-level-specific base and
    sensitivity, plus a mild rush-hour and weekend bump and Gaussian noise.
    """
    department_id = RNG.integers(0, 6, n_rows)  # 6 synthetic departments
    queue_length = RNG.integers(0, 40, n_rows)
    triage_level = RNG.choice(["P1", "P2", "P3"], n_rows, p=[0.15, 0.35, 0.50])
    staff_on_duty = RNG.integers(2, 15, n_rows)
    time_of_day = RNG.integers(0, 24, n_rows)
    day_of_week = RNG.integers(0, 7, n_rows)

    base = np.array([TRIAGE_BASE_MINUTES[t] for t in triage_level])
    sensitivity = np.array([TRIAGE_QUEUE_SENSITIVITY[t] for t in triage_level])

    rush_hour_bump = np.where((time_of_day >= 17) & (time_of_day <= 21), 8, 0)
    weekend_bump = np.where(day_of_week >= 5, 5, 0)
    understaffed_penalty = np.maximum(0, (queue_length / np.maximum(staff_on_duty, 1)) - 2) * 6

    wait_minutes = (
        base
        + queue_length * sensitivity
        - staff_on_duty * 0.8
        + rush_hour_bump
        + weekend_bump
        + understaffed_penalty
        + RNG.normal(0, 4, n_rows)
    )
    wait_minutes = np.clip(wait_minutes, 1, 480)

    return pd.DataFrame(
        {
            "department_id": department_id,
            "current_queue_length": queue_length,
            "triage_level": triage_level,
            "staff_on_duty": staff_on_duty,
            "time_of_day": time_of_day,
            "day_of_week": day_of_week,
            "wait_minutes": wait_minutes,
        }
    )


def generate_occupancy_time_series(n_departments: int = 6, hours: int = 24 * 60) -> pd.DataFrame:
    """
    Simulates hourly bed-occupancy % per department over `hours` hours,
    with a daily seasonal pattern (busier daytime/evenings), a slow
    trend, and noise. Used by statsmodels (Holt-Winters exponential
    smoothing) in train.py to derive realistic short-horizon occupancy
    trend labels for the overcrowding-risk model.
    """
    rows = []
    for dept in range(n_departments):
        t = np.arange(hours)
        daily_cycle = 15 * np.sin(2 * np.pi * (t % 24) / 24 - np.pi / 2)  # peaks mid-afternoon/evening
        slow_trend = 0.01 * t * RNG.uniform(0.3, 1.0)
        base_level = RNG.uniform(45, 65)
        noise = RNG.normal(0, 4, hours)

        # Occasional overcrowding "surge" events (mass-casualty, flu season
        # spikes, etc.) — without these, the model never sees the
        # high-occupancy / high-admission-rate combinations it most needs
        # to be reliable for, and gradient boosting extrapolates poorly
        # outside its training range.
        surge_starts = RNG.choice(hours, size=max(1, hours // 400), replace=False)
        surge = np.zeros(hours)
        admission_surge = np.zeros(hours)
        for s in surge_starts:
            duration = RNG.integers(3, 10)
            end = min(hours, s + duration)
            ramp = np.linspace(0, RNG.uniform(20, 35), end - s)
            surge[s:end] += ramp
            admission_surge[s:end] += np.linspace(0, RNG.uniform(3, 6), end - s)

        occupancy = base_level + daily_cycle + slow_trend + noise + surge
        occupancy = np.clip(occupancy, 5, 100)

        admission_rate = np.clip(
            2
            + 1.5 * np.sin(2 * np.pi * (t % 24) / 24 - np.pi / 2)
            + RNG.normal(0, 0.6, hours)
            + admission_surge,
            0,
            None,
        )

        rows.append(
            pd.DataFrame(
                {
                    "department_id": dept,
                    "hour_index": t,
                    "hour_of_day": t % 24,
                    "bed_occupancy_pct": occupancy,
                    "admission_rate_last_1h": admission_rate,
                }
            )
        )
    return pd.concat(rows, ignore_index=True)
