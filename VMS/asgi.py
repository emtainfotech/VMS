import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import EMTACHAT.routing # Make sure to import your app's routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VMS.settings')

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": get_asgi_application(),

    # WebSocket EMTACHAT handler
    "websocket": AuthMiddlewareStack(
        URLRouter(
            EMTACHAT.routing.websocket_urlpatterns
        )
    ),
})