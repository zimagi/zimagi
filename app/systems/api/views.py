from django.conf import settings
from django.http import StreamingHttpResponse

from rest_framework.views import APIView

from utility.encryption import Cipher

import sys
import json


class Command(APIView):

    name = None
    command = None


    @property
    def schema(self):
        return self.command.get_schema()


    def groups_allowed(self):
        return self.command.groups_allowed()


    def post(self, request, format = None):
        return self._request(request, request.POST, format)


    def _request(self, request, params, format = None):
        command = type(self.command)()
        command.parse_base()
        params = self._format_params(params)

        if params.get('no_parallel', False):
            settings.PARALLEL = False

        response = StreamingHttpResponse(
            streaming_content = command.handle_api(params),
            content_type = 'application/json'
        )
        response['Cache-Control'] = 'no-cache'
        return response

    def _format_params(self, data):
        cipher = Cipher.get()

        def process_item(key, value):
            key = cipher.decrypt(key)
            value = cipher.decrypt(value)
            return (key, value)
        
        return self.command.format_fields(data, process_item)
