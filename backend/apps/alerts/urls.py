from django.urls import path

from .views import AlertAcknowledgeView, AlertListView

urlpatterns = [
    path("all", AlertListView.as_view(), name="alert-list"),
    path("<uuid:pk>/acknowledge", AlertAcknowledgeView.as_view(), name="alert-acknowledge"),
]
