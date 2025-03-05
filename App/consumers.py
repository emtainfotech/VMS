import base64
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ScreenConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        image_data = data['image']
        
        # Decode and save the image if needed
        with open("media/Employee-Screen/employee.jpg", "wb") as f:
            f.write(base64.b64decode(image_data))
        
        # Send the image to the admin panel
        await self.send(text_data=json.dumps({"image": image_data}))
