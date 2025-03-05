import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from App.routing import websocket_urlpatterns  # Import WebSocket routes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VMS.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})
