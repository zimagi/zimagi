import logging

from starlette.requests import Request
from starlette.responses import JSONResponse

from .tools import index_tools
from .errors import ServerError


logger = logging.getLogger(__name__)


async def handle_status(request):
    return JSONResponse({"status": "OK"}, status_code=200)


def _initialize_connection(sessions, request, create=False):
    if not request.user.is_authenticated:
        raise ServerError("Access Denied", 401)

    try:
        if create:
            mcp = sessions.create(request.user.zimagi, "mcp-server")
        else:
            mcp = sessions.get(request.user.zimagi)

        index_tools(request.user.zimagi, mcp)

    except Exception as error:
        logger.error(error)
        raise ServerError(f"Initialization failure: {error}")

    return mcp


def create_connection_handler(sse, sessions):
    async def handle_connection(request):
        try:
            mcp = _initialize_connection(sessions, request, True)
        except ServerError as error:
            return JSONResponse({"error": str(error)}, status_code=error.code)

        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp.run(streams[0], streams[1], mcp.create_initialization_options())

    return handle_connection


def create_message_handler(sse, sessions):
    async def handle_message(scope, receive, send):
        try:
            mcp = _initialize_connection(sessions, Request(scope, receive))
        except ServerError as error:
            return JSONResponse({"error": str(error)}, status_code=error.code)

        return await sse.handle_post_message(scope, receive, send)

    return handle_message
