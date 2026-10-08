from django.urls import path

from .views import (
    PatientDetailView,
    PatientDischargeView,
    PatientIntakeView,
    PatientListView,
    PatientStatusUpdateView,
)

urlpatterns = [
    path("intake", PatientIntakeView.as_view(), name="patient-intake"),
    path("all", PatientListView.as_view(), name="patient-list"),
    path("<uuid:pk>", PatientDetailView.as_view(), name="patient-detail"),
    path("<uuid:pk>/status", PatientStatusUpdateView.as_view(), name="patient-status"),
    path("<uuid:pk>/discharge", PatientDischargeView.as_view(), name="patient-discharge"),
]
