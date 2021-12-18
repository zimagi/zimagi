from django.core.management import call_command
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from utility.display import format_exception_info

import logging


logger = logging.getLogger(__name__)


def format_error(request, error):
    query_params = ''
    if request.query_params:
        query_params = "?" + "&".join([ "{}={}".format(param, value) for param, value in request.query_params.items() ])

    return "[ {}:{}{} ] - {}\n\n{}".format(
        request.method,
        request.path,
        query_params,
        str(error),
        '> ' + "\n".join([ item.strip() for item in format_exception_info() ])
    )

def wrap_api_call(type, request, processor, message = None):
    try:
        return processor()

    except Exception as e:
        if not message:
            message = 'There was a problem servicing the request. The issue has been reported to the administrators.'
        elif callable(message):
            message = message(e)

        logger.error("{} API error: {}".format(type.title(), format_error(request, e)))
        return Response({ 'detail': message }, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


class Status(APIView):

    def get(self, request, format = None):

        def processor():
            call_command('check')
            return Response('System check successful')

        return wrap_api_call('status', request, processor,
            message = 'System check error'
        )
