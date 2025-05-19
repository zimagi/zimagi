"""
Zimagi ASGI config.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

import django
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Mount, Route
from systems.api.mcp.auth import TokenAuthBackend
from systems.api.mcp.routes import create_connection_handler, create_message_handler, handle_status
from systems.api.mcp.session import MCPSessions
from systems.models.overrides import *  # noqa: F401, F403
from utility.mutex import Mutex

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.full")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

django.setup()

sse = SseServerTransport("/messages/")
sessions = MCPSessions()


def get_asgi_application():
    from django.conf import settings

    return Starlette(
        debug=settings.DEBUG,
        routes=[
            Route("/", endpoint=create_connection_handler(sse, sessions)),
            Mount("/messages/", app=create_message_handler(sse, sessions)),
            Route("/status", endpoint=handle_status, methods=["GET"]),
        ],
        middleware=[Middleware(AuthenticationMiddleware, backend=TokenAuthBackend())],
    )


#
# Application Initialization
#
application = get_asgi_application()

Mutex.set("startup_{}".format(os.environ["ZIMAGI_SERVICE"]))
