from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.permissions import IsAdminOrDoctorOrNurse
from .models import Alert
from .serializers import AlertSerializer


class AlertListView(generics.ListAPIView):
    """GET /alerts/all — admin sees all; doctor/nurse see their department's alerts."""

    serializer_class = AlertSerializer
    permission_classes = [IsAdminOrDoctorOrNurse]

    def get_queryset(self):
        user = self.request.user
        qs = Alert.objects.all()
        if user.role != "ADMIN":
            qs = qs.filter(department=user.department)
        return qs


class AlertAcknowledgeView(APIView):
    """POST /alerts/:id/acknowledge."""

    permission_classes = [IsAdminOrDoctorOrNurse]

    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=["acknowledged_by", "acknowledged_at"])
        return Response(AlertSerializer(alert).data)
