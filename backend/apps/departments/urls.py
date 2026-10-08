from django.urls import path

from .views import (
    DepartmentDetailView,
    DepartmentListCreateView,
    DepartmentQueueView,
    DepartmentStatsView,
)

urlpatterns = [
    path("all", DepartmentListCreateView.as_view(), name="department-list"),
    path("<uuid:pk>", DepartmentDetailView.as_view(), name="department-detail"),
    path("<uuid:pk>/queue", DepartmentQueueView.as_view(), name="department-queue"),
    path("<uuid:pk>/stats", DepartmentStatsView.as_view(), name="department-stats"),
]
