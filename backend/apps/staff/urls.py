from django.urls import path

from .views import StaffDetailView, StaffDutyStatusView, StaffListCreateView

urlpatterns = [
    path("all", StaffListCreateView.as_view(), name="staff-list"),
    path("<uuid:pk>", StaffDetailView.as_view(), name="staff-detail"),
    path("<uuid:pk>/duty-status", StaffDutyStatusView.as_view(), name="staff-duty-status"),
]
