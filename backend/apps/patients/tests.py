from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.departments.models import Department
from apps.patients.models import Patient, PatientStatus, TriageLevel

User = get_user_model()


def _make_user(role, department=None, **extra):
    email = extra.pop("email", f"{role.lower()}@careflow.test")
    user = User.objects.create_user(
        username=extra.pop("username", role.lower()),
        email=email,
        password="test-pass-123",
        role=role,
        department=department,
    )
    return user


class KioskEndpointTests(APITestCase):
    """
    The kiosk endpoint is public and must NEVER leak patient-level data —
    this is a hard security requirement from the spec, not just a nicety.
    """

    def setUp(self):
        self.dept = Department.objects.create(name="Emergency", total_beds=10, occupied_beds=8)

    def test_kiosk_is_public_no_auth_required(self):
        response = self.client.get("/kiosk/wait-times")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_kiosk_response_never_contains_patient_fields(self):
        response = self.client.get("/kiosk/wait-times")
        body = response.json()
        self.assertTrue(len(body) >= 1)
        for row in body:
            self.assertEqual(set(row.keys()), {"department_name", "estimated_wait_minutes", "load_level"})
            # These would be a data leak if ever present:
            self.assertNotIn("id", row)
            self.assertNotIn("patient_id", row)
            self.assertNotIn("current_queue_length", row)


class PatientIntakeRBACTests(APITestCase):
    """Only Admin/Nurse may create intake records; Doctor and unauthenticated requests must be rejected."""

    def setUp(self):
        self.dept = Department.objects.create(name="Cardiology", total_beds=5, occupied_beds=1)
        self.nurse = _make_user("NURSE", department=self.dept)
        self.doctor = _make_user("DOCTOR", department=self.dept)
        self.payload = {"triage_level": TriageLevel.P2_URGENT, "department": str(self.dept.id)}

    def test_unauthenticated_intake_is_rejected(self):
        response = self.client.post("/patients/intake", self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_doctor_cannot_create_intake(self):
        self.client.force_authenticate(self.doctor)
        response = self.client.post("/patients/intake", self.payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nurse_can_create_intake(self):
        self.client.force_authenticate(self.nurse)
        response = self.client.post("/patients/intake", self.payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Patient.objects.first().status, PatientStatus.WAITING)


class DepartmentStatsTests(APITestCase):
    """Live-computed department metrics (queue length, occupancy) are correct."""

    def setUp(self):
        self.dept = Department.objects.create(name="Pediatrics", total_beds=20, occupied_beds=15)
        self.admin = _make_user("ADMIN")

    def test_bed_occupancy_percentage_is_computed_correctly(self):
        self.assertEqual(self.dept.bed_occupancy_pct, 75.0)

    def test_stats_endpoint_requires_auth(self):
        response = self.client.get(f"/departments/{self.dept.id}/stats")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_stats_endpoint_returns_live_metrics(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/departments/{self.dept.id}/stats")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["bed_occupancy_pct"], 75.0)
