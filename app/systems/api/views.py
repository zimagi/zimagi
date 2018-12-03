
from rest_framework.views import APIView
from rest_framework.response import Response

import sys
import io


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
        stdout = sys.stdout
        stream = io.StringIO()
        sys.stdout = stream

        self.command.handle(**self.command.get_options(options))

        sys.stdout = stdout
        return Response(stream.getvalue())
