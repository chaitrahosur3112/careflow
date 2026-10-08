import uuid

from django.conf import settings
from django.db import models


class AlertType(models.TextChoices):
    OVERCROWDING = "overcrowding", "Overcrowding Risk"
    UNDERSTAFFING = "understaffing", "Shift Understaffing"
    LONG_WAIT = "long_wait", "Long Wait-Time Patient"


class AlertSeverity(models.TextChoices):
    AMBER = "amber", "Amber (Warning)"
    RED = "red", "Red (Critical)"


class Alert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(
        "departments.Department", on_delete=models.CASCADE, related_name="alerts"
    )
    alert_type = models.CharField(max_length=32, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=AlertSeverity.choices)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="acknowledged_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["department", "severity"])]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.alert_type} — {self.department}"
