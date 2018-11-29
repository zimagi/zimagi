
from rest_framework.views import APIView
from rest_framework.response import Response

import sys
import io


class ExecuteCommand(APIView):

    name = None
    command = None


    def get(self, request, format = None):
        return self._request(request, request.GET, format)

    def post(self, request, format = None):
        return self._request(request, request.POST, format)


    def _request(self, request, options, format = None):
        stdout = sys.stdout
        stream = io.StringIO()
        sys.stdout = stream

        self.command.handle(**self.command.get_options(options))

        sys.stdout = stdout
        return Response(stream.getvalue())
