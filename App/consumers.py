import base64
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import os

class ScreenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.employee_id = self.scope["url_route"]["kwargs"]["employee_id"]
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        image_data = data.get("image", "")

        if image_data:
            # Create a directory if not exists
            save_path = f"media/screenshots/{self.employee_id}.jpg"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save the image
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(image_data))

            # Send confirmation back to admin panel
            await self.send(json.dumps({"status": "success", "employee_id": self.employee_id}))

    async def disconnect(self, close_code):
        print(f"Connection closed for Employee ID: {self.employee_id}")
