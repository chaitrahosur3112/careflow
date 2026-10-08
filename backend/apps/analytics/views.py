from django.db.models import Avg, Count
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.models import Patient
from apps.patients.permissions import IsAdminOrDoctorOrNurse, IsHospitalAdministrator
from apps.predictions.models import Prediction


class CanViewAnalytics(IsAdminOrDoctorOrNurse):
    """Admin/Doctor/Nurse (operational) OR Hospital Administrator (read-only) may view analytics."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) or IsHospitalAdministrator().has_permission(request, view)


class AdmissionTrendsView(APIView):
    """GET /analytics/admission-trends — daily patient intake counts."""

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        data = (
            Patient.objects.annotate(day=TruncDate("intake_time"))
            .values("day")
            .annotate(admissions=Count("id"))
            .order_by("day")
        )
        return Response(list(data))


class PeakHoursView(APIView):
    """GET /analytics/peak-hours — admissions bucketed by hour-of-day and day-of-week (heatmap source)."""

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        data = (
            Patient.objects.annotate(hour=ExtractHour("intake_time"), weekday=ExtractWeekDay("intake_time"))
            .values("weekday", "hour")
            .annotate(admissions=Count("id"))
            .order_by("weekday", "hour")
        )
        return Response(list(data))


class DepartmentBottlenecksView(APIView):
    """GET /analytics/department-bottlenecks — avg wait per department, worst first."""

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        from apps.departments.models import Department

        rows = []
        for dept in Department.objects.filter(is_active=True):
            rows.append({
                "department_id": str(dept.id),
                "department_name": dept.name,
                "average_wait_time_minutes": dept.average_wait_time_minutes,
                "current_queue_length": dept.current_queue_length,
                "bed_occupancy_pct": dept.bed_occupancy_pct,
            })
        rows.sort(key=lambda r: r["average_wait_time_minutes"], reverse=True)
        return Response(rows)


class ModelAccuracyView(APIView):
    """GET /analytics/model-accuracy — predicted vs actual, for admin-facing model validation display."""

    permission_classes = [CanViewAnalytics]

    def get(self, request):
        qs = Prediction.objects.exclude(actual_value__isnull=True)
        by_metric = {}
        for metric, _ in Prediction._meta.get_field("metric").choices:
            metric_qs = qs.filter(metric=metric)
            if not metric_qs.exists():
                by_metric[metric] = None
                continue
            errors = [abs(p.predicted_value - p.actual_value) for p in metric_qs]
            mae = sum(errors) / len(errors)
            rmse = (sum(e ** 2 for e in errors) / len(errors)) ** 0.5
            by_metric[metric] = {"mae": round(mae, 2), "rmse": round(rmse, 2), "sample_size": len(errors)}
        return Response(by_metric)
