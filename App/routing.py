from django.urls import path
from App.consumers import ScreenConsumer
from channels.routing import ProtocolTypeRouter, URLRouter

websocket_urlpatterns = [
    path("ws/screen/<str:employee_id>/", ScreenConsumer.as_asgi()),
]
