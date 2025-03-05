from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from App.consumers import ScreenConsumer  # Ensure this import is correct

websocket_urlpatterns = [
    re_path(r'ws/screen/$', ScreenConsumer.as_asgi()),  # ✅ WebSocket path
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
