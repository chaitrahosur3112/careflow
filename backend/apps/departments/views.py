from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.models import Patient
from apps.patients.permissions import IsAdmin, IsAdminOrDoctorOrNurse, IsHospitalAdministrator
from apps.patients.serializers import PatientSerializer
from .models import Department
from .serializers import DepartmentSerializer, DepartmentStatsSerializer


class IsAdminOrReadOnlyAnalyticsRole(permissions.BasePermission):
    """Admin can write; Doctor/Nurse/HospitalAdministrator can read."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return request.user.role in {"ADMIN", "DOCTOR", "NURSE", "HOSPITAL_ADMINISTRATOR"}
        return request.user.role == "ADMIN"


class DepartmentListCreateView(generics.ListCreateAPIView):
    """GET /departments/all, POST /departments/all (admin creates new department)."""

    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnlyAnalyticsRole]


class DepartmentDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /departments/:id."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrReadOnlyAnalyticsRole]


class DepartmentQueueView(APIView):
    """GET /departments/:id/queue — live waiting-room list for this department."""

    permission_classes = [IsAdminOrDoctorOrNurse]

    def get(self, request, pk):
        patients = Patient.objects.filter(department_id=pk, status="waiting")
        return Response(PatientSerializer(patients, many=True).data)


class DepartmentStatsView(APIView):
    """GET /departments/:id/stats — live computed load metrics for dashboards."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        dept = Department.objects.get(pk=pk)
        data = {
            "id": dept.id,
            "name": dept.name,
            "total_beds": dept.total_beds,
            "occupied_beds": dept.occupied_beds,
            "bed_occupancy_pct": dept.bed_occupancy_pct,
            "current_queue_length": dept.current_queue_length,
            "staff_on_duty_count": dept.staff_on_duty_count,
            "average_wait_time_minutes": dept.average_wait_time_minutes,
        }
        return Response(DepartmentStatsSerializer(data).data)
