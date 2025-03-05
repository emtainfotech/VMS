from channels.generic.websocket import AsyncWebsocketConsumer
import json
import os
import base64

class ScreenConsumer(AsyncWebsocketConsumer):
    connected_users = {}  # Dictionary to store connections

    async def connect(self):
        self.employee_id = self.scope["url_route"]["kwargs"]["emp_id"]
        self.connected_users[self.employee_id] = self
        await self.accept()
        print(f"✅ Connection established for: {self.employee_id}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        image_data = data.get("image", "")

        if image_data:
            save_path = f"media/screenshots/{self.employee_id}.jpg"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(base64.b64decode(image_data))

            await self.send(json.dumps({"status": "success", "employee_id": self.employee_id}))

    async def disconnect(self, close_code):
        print(f"❌ Disconnected: {self.employee_id}")
        if self.employee_id in self.connected_users:
            del self.connected_users[self.employee_id]
