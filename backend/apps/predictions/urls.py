from django.urls import path

from .views import OvercrowdingRiskView, StaffingRecommendationView, WaitTimePredictionView

urlpatterns = [
    path("wait-time", WaitTimePredictionView.as_view(), name="predict-wait-time"),
    path("overcrowding-risk", OvercrowdingRiskView.as_view(), name="predict-overcrowding-risk"),
    path("staffing-recommendation", StaffingRecommendationView.as_view(), name="predict-staffing"),
]
