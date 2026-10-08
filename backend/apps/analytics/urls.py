from django.urls import path

from .views import (
    AdmissionTrendsView,
    DepartmentBottlenecksView,
    ModelAccuracyView,
    PeakHoursView,
)

urlpatterns = [
    path("admission-trends", AdmissionTrendsView.as_view(), name="analytics-admission-trends"),
    path("peak-hours", PeakHoursView.as_view(), name="analytics-peak-hours"),
    path("department-bottlenecks", DepartmentBottlenecksView.as_view(), name="analytics-bottlenecks"),
    path("model-accuracy", ModelAccuracyView.as_view(), name="analytics-model-accuracy"),
]
