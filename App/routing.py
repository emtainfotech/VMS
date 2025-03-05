from django.urls import path
from App.consumers import ScreenConsumer  # Correcting the import

websocket_urlpatterns = [
    path("ws/screen/<str:employee_id>/", ScreenConsumer.as_asgi()),  # Ensure parameter name matches
]
