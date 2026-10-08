from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.departments.models import Department
from .models import Patient, PatientStatus, QueueEvent, QueueEventType
from .permissions import IsAdminOrDoctorOrNurse, IsAdminOrNurse
from .serializers import (
    KioskWaitTimeSerializer,
    PatientIntakeSerializer,
    PatientSerializer,
    PatientStatusUpdateSerializer,
)


def _broadcast_queue_update(department_id):
    """Push a live update to the WebSocket group for this department's queue board."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"queue_{department_id}",
        {"type": "queue.update", "department_id": str(department_id)},
    )


class PatientIntakeView(generics.CreateAPIView):
    """POST /patients/intake — nurse/triage adds a patient to the queue."""

    serializer_class = PatientIntakeSerializer
    permission_classes = [IsAdminOrNurse]

    def perform_create(self, serializer):
        patient = serializer.save()
        QueueEvent.objects.create(
            patient=patient, event_type=QueueEventType.INTAKE, performed_by=self.request.user
        )
        _broadcast_queue_update(patient.department_id)


class PatientListView(generics.ListAPIView):
    """GET /patients/all — clinical roles see patients scoped to their own department (admin sees all)."""

    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrDoctorOrNurse]

    def get_queryset(self):
        user = self.request.user
        qs = Patient.objects.all()
        if user.role != "ADMIN":
            qs = qs.filter(department=user.department)
        return qs


class PatientDetailView(generics.RetrieveAPIView):
    """GET /patients/:id."""

    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAdminOrDoctorOrNurse]


class PatientStatusUpdateView(APIView):
    """PATCH /patients/:id/status — waiting / in-treatment / discharged."""

    permission_classes = [IsAdminOrDoctorOrNurse]

    def patch(self, request, pk):
        patient = Patient.objects.get(pk=pk)
        serializer = PatientStatusUpdateSerializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        QueueEvent.objects.create(
            patient=patient,
            event_type=QueueEventType.STATUS_CHANGE,
            performed_by=request.user,
            notes=f"status -> {patient.status}",
        )
        _broadcast_queue_update(patient.department_id)
        return Response(PatientSerializer(patient).data)


class PatientDischargeView(APIView):
    """POST /patients/:id/discharge — closes the queue record."""

    permission_classes = [IsAdminOrDoctorOrNurse]

    def post(self, request, pk):
        patient = Patient.objects.get(pk=pk)
        patient.status = PatientStatus.DISCHARGED
        patient.discharge_time = timezone.now()
        patient.save(update_fields=["status", "discharge_time"])
        QueueEvent.objects.create(
            patient=patient, event_type=QueueEventType.DISCHARGE, performed_by=request.user
        )
        _broadcast_queue_update(patient.department_id)
        return Response(PatientSerializer(patient).data, status=status.HTTP_200_OK)


class KioskWaitTimesView(APIView):
    """
    GET /kiosk/wait-times — PUBLIC, no auth. Anonymized wait estimates ONLY.
    Never exposes patient IDs, counts, or names — field-level lockdown per spec.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "kiosk"

    def get(self, request):
        results = []
        for dept in Department.objects.filter(is_active=True):
            pct = dept.bed_occupancy_pct
            load_level = "high" if pct >= 95 else "medium" if pct >= 80 else "low"
            results.append(
                {
                    "department_name": dept.name,
                    "estimated_wait_minutes": dept.average_wait_time_minutes,
                    "load_level": load_level,
                }
            )
        return Response(KioskWaitTimeSerializer(results, many=True).data)
