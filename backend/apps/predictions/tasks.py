from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.alerts.models import Alert, AlertSeverity, AlertType
from apps.departments.models import Department


@shared_task
def recompute_all_predictions():
    """
    Periodic Celery Beat task (every 5 min). Re-checks bed occupancy per
    department against the configured thresholds and raises/keeps overcrowding
    alerts up to date. Real wait-time/risk model calls happen on-demand via
    the /predictions/* endpoints (see apps.predictions.views) to keep this
    task lightweight and avoid hammering the ML microservice on a timer.
    """
    amber = settings.OVERCROWDING_AMBER_THRESHOLD
    red = settings.OVERCROWDING_RED_THRESHOLD

    for dept in Department.objects.filter(is_active=True):
        pct = dept.bed_occupancy_pct
        if pct >= red:
            _raise_alert_if_new(dept, AlertSeverity.RED, f"{dept.name} at {pct}% bed occupancy — critical.")
        elif pct >= amber:
            _raise_alert_if_new(dept, AlertSeverity.AMBER, f"{dept.name} at {pct}% bed occupancy — approaching capacity.")

        for patient in dept.patients.filter(status="waiting"):
            if patient.time_in_system_minutes > settings.LONG_WAIT_THRESHOLD_MINUTES:
                Alert.objects.get_or_create(
                    department=dept,
                    alert_type=AlertType.LONG_WAIT,
                    message=f"Patient {str(patient.id)[:8]} waiting {int(patient.time_in_system_minutes)} min in {dept.name}.",
                    defaults={"severity": AlertSeverity.AMBER},
                )


def _raise_alert_if_new(department, severity, message):
    recent_unacknowledged = Alert.objects.filter(
        department=department, alert_type=AlertType.OVERCROWDING, acknowledged_at__isnull=True
    ).exists()
    if not recent_unacknowledged:
        Alert.objects.create(
            department=department,
            alert_type=AlertType.OVERCROWDING,
            severity=severity,
            message=message,
            created_at=timezone.now(),
        )
