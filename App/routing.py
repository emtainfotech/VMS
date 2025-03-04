from django.urls import path
from App.consumers import ScreenConsumer

websocket_urlpatterns = [
    path("ws/screen/", ScreenConsumer.as_asgi()),
]
