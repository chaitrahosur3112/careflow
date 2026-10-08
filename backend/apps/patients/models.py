import uuid

from django.conf import settings
from django.db import models


class TriageLevel(models.TextChoices):
    P1_CRITICAL = "P1", "P1 Critical (immediate)"
    P2_URGENT = "P2", "P2 Urgent (within 30 min)"
    P3_STANDARD = "P3", "P3 Standard (within 2 hours)"


class PatientStatus(models.TextChoices):
    WAITING = "waiting", "Waiting"
    IN_TREATMENT = "in_treatment", "In Treatment"
    DISCHARGED = "discharged", "Discharged"


class Patient(models.Model):
    """
    Anonymized queue record. Never store real names — patient_id is a
    generated UUID used only to track flow through the department.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_level = models.CharField(max_length=2, choices=TriageLevel.choices)
    department = models.ForeignKey(
        "departments.Department", on_delete=models.CASCADE, related_name="patients"
    )
    status = models.CharField(
        max_length=20, choices=PatientStatus.choices, default=PatientStatus.WAITING
    )
    intake_time = models.DateTimeField(auto_now_add=True)
    discharge_time = models.DateTimeField(null=True, blank=True)
    assigned_nurse = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_patients",
    )

    class Meta:
        ordering = ["-intake_time"]
        indexes = [
            models.Index(fields=["department", "status"]),
            models.Index(fields=["triage_level"]),
        ]

    def __str__(self):
        return f"Patient {str(self.id)[:8]} — {self.triage_level} — {self.status}"

    @property
    def time_in_system_minutes(self):
        from django.utils import timezone

        end = self.discharge_time or timezone.now()
        return round((end - self.intake_time).total_seconds() / 60, 1)


class QueueEventType(models.TextChoices):
    INTAKE = "intake", "Intake"
    STATUS_CHANGE = "status_change", "Status Change"
    DISCHARGE = "discharge", "Discharge"


class QueueEvent(models.Model):
    """Immutable audit-trail record: who did what, to which patient, when."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=20, choices=QueueEventType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="queue_events"
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.event_type} — {self.patient_id} @ {self.timestamp}"
