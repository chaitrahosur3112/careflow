import json

from channels.generic.websocket import AsyncWebsocketConsumer


class QueueUpdatesConsumer(AsyncWebsocketConsumer):
    """
    ws://.../ws/queue-updates/?department=<uuid>
    Pushes a lightweight "something changed, refetch" signal — the frontend
    re-fetches /departments/:id/queue and /departments/:id/stats on receipt.
    Keeping the payload thin avoids ever pushing patient data over a channel
    that isn't individually authenticated per department.
    """

    async def connect(self):
        self.department_id = self.scope["url_route"]["kwargs"]["department_id"]
        self.group_name = f"queue_{self.department_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def queue_update(self, event):
        await self.send(text_data=json.dumps({"type": "queue_update", "department_id": event["department_id"]}))
