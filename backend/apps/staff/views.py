from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.permissions import IsAdmin, IsAdminOrDoctorOrNurse
from .models import StaffShift
from .serializers import StaffShiftSerializer


class StaffListCreateView(generics.ListCreateAPIView):
    """GET /staff/all (view shifts), POST (admin schedules a new shift)."""

    queryset = StaffShift.objects.all()
    serializer_class = StaffShiftSerializer
    permission_classes = [IsAdminOrDoctorOrNurse]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return super().get_permissions()


class StaffDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /staff/:id."""

    queryset = StaffShift.objects.all()
    serializer_class = StaffShiftSerializer
    permission_classes = [IsAdmin]


class StaffDutyStatusView(APIView):
    """PATCH /staff/:id/duty-status — toggle is_on_duty (clock in/out)."""

    permission_classes = [IsAdminOrDoctorOrNurse]

    def patch(self, request, pk):
        shift = get_object_or_404(StaffShift, pk=pk)
        shift.is_on_duty = request.data.get("is_on_duty", shift.is_on_duty)
        shift.save(update_fields=["is_on_duty"])
        return Response(StaffShiftSerializer(shift).data)
