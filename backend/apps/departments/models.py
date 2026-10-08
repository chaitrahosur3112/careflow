import uuid

from django.db import models


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    total_beds = models.PositiveIntegerField(default=0)
    occupied_beds = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def bed_occupancy_pct(self) -> float:
        if self.total_beds == 0:
            return 0.0
        return round((self.occupied_beds / self.total_beds) * 100, 1)

    @property
    def current_queue_length(self) -> int:
        return self.patients.filter(status="waiting").count()

    @property
    def staff_on_duty_count(self) -> int:
        from apps.staff.models import StaffShift

        return StaffShift.objects.filter(department=self, is_on_duty=True).count()

    @property
    def average_wait_time_minutes(self):
        """Average time-in-system (minutes) for currently waiting patients."""
        from django.utils import timezone

        waiting = self.patients.filter(status="waiting")
        if not waiting.exists():
            return 0
        now = timezone.now()
        total_minutes = sum((now - p.intake_time).total_seconds() / 60 for p in waiting)
        return round(total_minutes / waiting.count(), 1)
