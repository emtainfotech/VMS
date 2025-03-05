from django.urls import path
from VMS.consumers import MyWebSocketConsumer  # Import your WebSocket consumer

websocket_urlpatterns = [
    path("ws/screen/<str:emp_id>/", MyWebSocketConsumer.as_asgi()),
]
