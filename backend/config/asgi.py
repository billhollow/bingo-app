"""
ASGI config for config project.

Exposes the ASGI callable as a module-level variable named ``application``.
HTTP requests go straight to Django. Websocket connections are authenticated
per-connection by RoomConsumer itself (a bearer token in the query string,
same scheme as the REST API) rather than Django's session-based
AuthMiddlewareStack, since there's no Django auth User in this app.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from core.routing import websocket_urlpatterns  # noqa: E402  (must import after django setup)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
