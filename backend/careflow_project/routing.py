from django.urls import re_path

from apps.patients.consumers import QueueUpdatesConsumer

websocket_urlpatterns = [
    re_path(r"ws/queue-updates/(?P<department_id>[0-9a-f-]+)/$", QueueUpdatesConsumer.as_asgi()),
]
