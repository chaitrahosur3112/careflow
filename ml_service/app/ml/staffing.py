"""
Rule-based staffing recommendation engine.

Deliberately NOT a black-box ML model: hospital staffing calls need to be
explainable, so this composes a plain-English recommendation from the
current load, staff on duty, and the (ML-predicted) overcrowding risk
score passed in by the caller. Thresholds mirror the ones used for
overcrowding alerts, so the recommendation and the alert always agree.

`current_load` is a patient COUNT (current queue length), not a
percentage — see schemas.StaffingRecommendationRequest.
"""

AMBER_THRESHOLD = 80
RED_THRESHOLD = 95

LOAD_PER_STAFF_TARGET = 4.0  # target patients-in-queue per staff member
MAX_RECOMMENDED_ADDITION = 5  # a single recommendation call should never suggest an unrealistic shift change


def _extra_staff_needed(current_load: float, staff_on_duty: int) -> int:
    raw = round((current_load / LOAD_PER_STAFF_TARGET) - staff_on_duty)
    return max(1, min(raw, MAX_RECOMMENDED_ADDITION))


def recommend_staffing(current_load: float, staff_on_duty: int, predicted_risk: float) -> str:
    load_per_staff = current_load / staff_on_duty if staff_on_duty > 0 else current_load

    if predicted_risk >= RED_THRESHOLD:
        extra_needed = _extra_staff_needed(current_load, staff_on_duty)
        return (
            f"Department is approaching critical load (risk {predicted_risk:.0f}/100) — "
            f"recommend adding {extra_needed} nurse(s) to the current shift immediately."
        )

    if predicted_risk >= AMBER_THRESHOLD:
        extra_needed = _extra_staff_needed(current_load, staff_on_duty)
        return (
            f"Department is trending toward high load (risk {predicted_risk:.0f}/100) — "
            f"recommend adding {extra_needed} nurse(s) to the next shift."
        )

    if load_per_staff > LOAD_PER_STAFF_TARGET:
        return (
            f"Current staffing is below the target ratio ({load_per_staff:.1f} patients per staff member) "
            f"even though overcrowding risk is currently low — consider adding 1 nurse if this persists."
        )

    return "Current staffing levels are adequate for the predicted load — no action needed."
