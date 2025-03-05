import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import App.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VMS.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(App.routing.websocket_urlpatterns)
    ),
})
