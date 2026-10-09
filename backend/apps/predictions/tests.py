import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.departments.models import Department
from apps.predictions.models import Prediction, PredictionMetric
from apps.predictions.views import serialize_payload

User = get_user_model()


class PredictionsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(name="Emergency", total_beds=20, occupied_beds=14)
        self.user = User.objects.create_user(
            username="doctor_test",
            email="doctor_test@careflow.demo",
            password="TestPassword123!",
            role="DOCTOR",
            department=self.department,
        )

    def test_serialize_payload_converts_uuids(self):
        sample_uuid = uuid.uuid4()
        payload = {
            "department_id": sample_uuid,
            "nested": {"other_id": sample_uuid, "count": 10},
            "list": [sample_uuid, "string", 42],
        }
        serialized = serialize_payload(payload)
        self.assertEqual(serialized["department_id"], str(sample_uuid))
        self.assertEqual(serialized["nested"]["other_id"], str(sample_uuid))
        self.assertEqual(serialized["list"][0], str(sample_uuid))
        self.assertEqual(serialized["nested"]["count"], 10)

    def test_prediction_endpoints_require_authentication(self):
        resp_wait = self.client.post(reverse("predict-wait-time"), {})
        self.assertEqual(resp_wait.status_code, status.HTTP_401_UNAUTHORIZED)

        resp_risk = self.client.post(reverse("predict-overcrowding-risk"), {})
        self.assertEqual(resp_risk.status_code, status.HTTP_401_UNAUTHORIZED)

        resp_staffing = self.client.post(reverse("predict-staffing"), {})
        self.assertEqual(resp_staffing.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.predictions.views.requests.post")
    def test_wait_time_prediction_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "department_id": str(self.department.id),
            "predicted_wait_minutes": 25.4,
            "model_version": "v1",
        }
        mock_post.return_value.raise_for_status.return_value = None

        self.client.force_authenticate(user=self.user)
        payload = {
            "department_id": str(self.department.id),
            "current_queue_length": 5,
            "triage_level": "P2",
            "staff_on_duty": 3,
            "time_of_day": 14,
            "day_of_week": 2,
        }
        resp = self.client.post(reverse("predict-wait-time"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["predicted_wait_minutes"], 25.4)

        # Check that Prediction was persisted
        pred = Prediction.objects.filter(department=self.department, metric=PredictionMetric.WAIT_TIME).first()
        self.assertIsNotNone(pred)
        self.assertEqual(pred.predicted_value, 25.4)

    @patch("apps.predictions.views.requests.post")
    def test_overcrowding_risk_prediction_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "department_id": str(self.department.id),
            "risk_score": 85.0,
            "severity": "amber",
            "model_version": "v1",
        }
        mock_post.return_value.raise_for_status.return_value = None

        self.client.force_authenticate(user=self.user)
        payload = {
            "department_id": str(self.department.id),
            "admission_rate_last_1h": 8.0,
            "bed_occupancy_pct": 82.5,
            "hour_of_day": 14,
        }
        resp = self.client.post(reverse("predict-overcrowding-risk"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["risk_score"], 85.0)

        # Check that Prediction was persisted
        pred = Prediction.objects.filter(
            department=self.department, metric=PredictionMetric.OVERCROWDING_RISK
        ).first()
        self.assertIsNotNone(pred)
        self.assertEqual(pred.predicted_value, 85.0)

    @patch("apps.predictions.views.requests.post")
    def test_staffing_recommendation_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "department_id": str(self.department.id),
            "recommendation": "Recommend adding 1 nurse to current shift.",
        }
        mock_post.return_value.raise_for_status.return_value = None

        self.client.force_authenticate(user=self.user)
        payload = {
            "department_id": str(self.department.id),
            "current_load": 12.0,
            "staff_on_duty": 3,
            "predicted_risk": 85.0,
        }
        resp = self.client.post(reverse("predict-staffing"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("recommendation", resp.data)
