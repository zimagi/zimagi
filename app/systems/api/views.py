
from django.http import StreamingHttpResponse

from rest_framework.views import APIView

import sys


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


    def _request(self, request, options, format = None):
        response = StreamingHttpResponse(
            streaming_content = self.command.handle_api(options),
            content_type = 'application/json'
        )
        response['Cache-Control'] = 'no-cache'
        return response
