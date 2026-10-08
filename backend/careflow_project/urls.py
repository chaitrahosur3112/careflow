from django.contrib import admin
from django.urls import include, path

from apps.patients.views import KioskWaitTimesView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("apps.users.urls")),
    path("users/", include("apps.users.urls")),
    path("patients/", include("apps.patients.urls")),
    path("departments/", include("apps.departments.urls")),
    path("staff/", include("apps.staff.urls")),
    path("predictions/", include("apps.predictions.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("analytics/", include("apps.analytics.urls")),
    # Public, unauthenticated kiosk endpoint
    path("kiosk/wait-times", KioskWaitTimesView.as_view(), name="kiosk-wait-times"),
]
