import uuid
import requests
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Prediction, PredictionMetric
from .serializers import (
    OvercrowdingRiskRequestSerializer,
    StaffingRecommendationRequestSerializer,
    WaitTimeRequestSerializer,
)


def serialize_payload(payload):
    """
    Recursively converts UUID and other non-JSON-serializable objects into strings.
    Prevents TypeError: Object of type UUID is not JSON serializable when sending payloads to ML service.
    """
    if isinstance(payload, dict):
        return {k: serialize_payload(v) for k, v in payload.items()}
    elif isinstance(payload, (list, tuple)):
        return [serialize_payload(v) for v in payload]
    elif isinstance(payload, uuid.UUID):
        return str(payload)
    return payload


class BaseMLProxyView(APIView):
    """
    Shared logic for calling the FastAPI ML microservice. Any downstream
    connection/timeout error surfaces as a clean 503 instead of a stack trace.
    """

    permission_classes = [permissions.IsAuthenticated]
    ml_path = None

    def call_ml_service(self, payload):
        url = f"{settings.ML_SERVICE_URL}{self.ml_path}"
        try:
            clean_payload = serialize_payload(payload)
            resp = requests.post(url, json=clean_payload, timeout=5)
            resp.raise_for_status()
            return resp.json(), None
        except requests.RequestException as exc:
            return None, str(exc)


class WaitTimePredictionView(BaseMLProxyView):
    """POST /predictions/wait-time"""

    ml_path = "/predict/wait-time"

    def post(self, request):
        serializer = WaitTimeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data, error = self.call_ml_service(serializer.validated_data)
        if error:
            return Response({"detail": f"ML service unavailable: {error}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        Prediction.objects.create(
            department_id=serializer.validated_data["department_id"],
            metric=PredictionMetric.WAIT_TIME,
            predicted_value=data.get("predicted_wait_minutes", 0),
            model_version=data.get("model_version", "v1"),
        )
        return Response(data)


class OvercrowdingRiskView(BaseMLProxyView):
    """POST /predictions/overcrowding-risk"""

    ml_path = "/predict/overcrowding-risk"

    def post(self, request):
        serializer = OvercrowdingRiskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data, error = self.call_ml_service(serializer.validated_data)
        if error:
            return Response({"detail": f"ML service unavailable: {error}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        Prediction.objects.create(
            department_id=serializer.validated_data["department_id"],
            metric=PredictionMetric.OVERCROWDING_RISK,
            predicted_value=data.get("risk_score", 0),
            model_version=data.get("model_version", "v1"),
        )
        return Response(data)


class StaffingRecommendationView(BaseMLProxyView):
    """POST /predictions/staffing-recommendation"""

    ml_path = "/recommend/staffing"

    def post(self, request):
        serializer = StaffingRecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data, error = self.call_ml_service(serializer.validated_data)
        if error:
            return Response({"detail": f"ML service unavailable: {error}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(data)
