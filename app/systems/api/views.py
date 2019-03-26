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


    def get_env(self):
        return self.command.get_env()

    def groups_allowed(self):
        return self.command.groups_allowed()


    def post(self, request, format = None):
        return self._request(request, request.POST, format)


    def _request(self, request, options, format = None):
        options = self._format_options(options)
        command = self._get_command(options)

        response = StreamingHttpResponse(
            streaming_content = command.handle_api(options),
            content_type = 'application/json'
        )
        response['Cache-Control'] = 'no-cache'
        return response

    def _get_command(self, options):
        command = type(self.command)(
            self.command.name,
            self.command.parent_instance
        )
        command.bootstrap(options)
        command.parse_base()
        return command

    def _format_options(self, options):
        cipher = Cipher.get('params')

        def process_item(key, value):
            key = cipher.decrypt(key)
            value = cipher.decrypt(value)
            return (key, value)

        return self.command.format_fields(options, process_item)
