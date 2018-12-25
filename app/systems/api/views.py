
from django.http import StreamingHttpResponse

from rest_framework.views import APIView

from utility.encryption import Cipher

import sys
import json


class ExecuteCommand(APIView):

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
        params = self._format_params(params)
        response = StreamingHttpResponse(
            streaming_content = self.command.handle_api(params),
            content_type = 'application/json'
        )
        response['Cache-Control'] = 'no-cache'
        return response

    def _format_params(self, data):
        fields = self.schema.get_fields()
        cipher = Cipher.get()
        params = {}

        for key, value in data.items():
            key = cipher.decrypt(key)
            value = cipher.decrypt(value)
            type = fields[key].type

            if type == 'dictfield':
                params[key] = json.loads(value)
            elif type == 'listfield':
                params[key] = json.loads(value)    
            else:
                params[key] = value

        return params
