import uuid

from django.conf import settings
from django.db import models


class StaffShift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff_member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shifts"
    )
    department = models.ForeignKey(
        "departments.Department", on_delete=models.CASCADE, related_name="shifts"
    )
    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()
    is_on_duty = models.BooleanField(default=False)

    class Meta:
        ordering = ["-shift_start"]
        indexes = [models.Index(fields=["department", "is_on_duty"])]

    def __str__(self):
        return f"{self.staff_member} @ {self.department} [{self.shift_start:%H:%M}-{self.shift_end:%H:%M}]"
