import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    DOCTOR = "DOCTOR", "Doctor"
    NURSE = "NURSE", "Nurse / Triage Staff"
    HOSPITAL_ADMINISTRATOR = "HOSPITAL_ADMINISTRATOR", "Hospital Administrator (analytics only)"
    # KIOSK is not a real logged-in role — kiosk endpoints are unauthenticated.


class User(AbstractUser):
    """
    Custom user model. Email is the login identifier; role drives RBAC
    across every protected endpoint (see apps.patients.permissions).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=Role.choices)
    department = models.ForeignKey(
        "departments.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_members",
        help_text="Required for DOCTOR and NURSE roles; irrelevant for ADMIN/HOSPITAL_ADMINISTRATOR.",
    )
    is_active_staff = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [models.Index(fields=["role"]), models.Index(fields=["email"])]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
