import logging

from django.core.management import call_command
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView
from systems.api.response import EncryptedResponse
from utility.display import format_exception_info

logger = logging.getLogger(__name__)


def format_error(request, error):
    query_params = ""
    if request.query_params:
        query_params = "?" + "&".join([f"{param}={value}" for param, value in request.query_params.items()])

    return "[ {}:{}{} ] - {}\n\n{}".format(
        request.method,
        request.path,
        query_params,
        str(error),
        "> " + "\n".join([item.strip() for item in format_exception_info()]),
    )


def wrap_api_call(type, request, processor, message=None, show_error=False, encrypt=True, api_type=None, status=None):
    if status is None:
        status = HTTP_500_INTERNAL_SERVER_ERROR
    try:
        return processor()

    except Exception as e:
        if not message:
            message = (
                "There was a problem servicing the request. The issue has been reported to the administrators"
                if not show_error
                else str(e)
            )
        elif callable(message):
            message = message(e)

        logger.error(
            "{} API error <{}>: {}".format(
                type.title(), request.user.name if request.user else "anonymous", format_error(request, e)
            )
        )

        if encrypt:
            return EncryptedResponse(
                data={"detail": message}, status=status, user=request.user.name if request.user else None, api_type=api_type
            )
        return Response(data={"detail": message}, status=status)


class Status(APIView):
    encryption = False

    def get(self, request, format=None):
        def processor():
            call_command("check")
            return Response({"message": "System check successful", "encryption": self.encryption})

        return wrap_api_call("status", request, processor, message="System check error", encrypt=False)
