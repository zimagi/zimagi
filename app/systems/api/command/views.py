from django.http import StreamingHttpResponse
from rest_framework.views import APIView

from systems.api.views import wrap_api_call
from utility.encryption import Cipher

import logging


logger = logging.getLogger(__name__)


class Command(APIView):

    name = None
    command = None


    @property
    def schema(self):
        return self.command.get_schema()


    def get_env(self):
        return self.command.get_env()

    def get_host(self):
        return self.command.get_host()


    def check_execute(self, user):
        return self.command.check_execute(user)


    def post(self, request, format = None):

        def processor():
            options = self._format_options(request.POST)
            command = type(self.command)(
                self.command.name,
                self.command.parent_instance
            ).bootstrap(options, True)

            response = StreamingHttpResponse(
                streaming_content = command.handle_api(options),
                content_type = 'application/json'
            )
            response['Cache-Control'] = 'no-cache'
            return response

        def error_handler(error):
            return str(error)

        return wrap_api_call('command', request, processor,
            message = error_handler
        )


    def _format_options(self, options):
        cipher = Cipher.get('params')

        def process_item(key, value):
            return (key, cipher.decrypt(value))

        return self.command.format_fields(options, process_item)
