from collections import OrderedDict
from requests.exceptions import ConnectionError

from .. import exceptions, utility, transports, schema
from . import response, messages

import logging
import yaml


logger = logging.getLogger(__name__)


class CommandHTTPSTransport(transports.BaseTransport):

    def __init__(self,
        headers = None,
        auth = None,
        options_callback = None,
        message_callback = None,
        encryption_key = None
    ):
        super().__init__(
            headers = headers,
            auth = auth,
            encryption_key = encryption_key
        )
        self._options_callback = options_callback
        self._message_callback = message_callback


    def transition(self, link, decoders, params = None):
        params = self.get_params(link, params)
        url = self.get_url(link.url, params.path)
        headers = self.get_headers(url, decoders)
        headers.update(self._headers)

        if link.action == 'get':
            # Schema
            try:
                result = self.request_page(url, headers, params, decoders)
                if isinstance(result, schema.Error):
                    raise exceptions.CommandError(result['detail'])
                return result

            except ConnectionError as error:
                raise exceptions.CommandConnectionError(error)
        else:
            # Command
            if self._options_callback and callable(self._options_callback):
                self._options_callback(params.data)
            try:
                return self.request_stream(url, headers, params, decoders)
            except ConnectionError as error:
                raise exceptions.CommandConnectionError(error)


    def request_stream(self, url, headers, params, decoders):
        session = self.init_session()
        request = self._build_post_request(session, url, headers, params)
        settings = session.merge_environment_settings(
            request.url, None, True, False, None
        )
        logger.debug("Stream {} request headers: {}".format(request.url, request.headers))

        request_response = session.send(request, **settings)
        command_response = response.CommandResponse()

        if request_response.status_code >= 400:
            raise exceptions.CommandResponseError(utility.format_response_error(request_response))
        try:
            for line in request_response.iter_lines():
                message = messages.Message.get(
                    self._decode_message(request_response, line, decoders),
                    self._cipher.key
                )
                if self._message_callback and callable(self._message_callback):
                    self._message_callback(message)

                command_response.add(message)

        except Exception as error:
            logger.debug("Stream {} error response headers: {}".format(request.url, request_response.headers))
            logger.debug("Stream {} error response params:\n\n{}".format(request.url, yaml.dump(params.data)))
            logger.debug("Stream {} error status code: {}".format(request.url, request_response.status_code))
            raise error

        return command_response


    def _decode_message(self, response, data, decoders):
        result = None

        if data:
            content_type = response.headers.get('content-type')
            codec = self._negotiate_decoder(decoders, content_type)

            options = {
                'base_url': response.url
            }
            if 'content-type' in response.headers:
                options['content_type'] = response.headers['content-type']
            if 'content-disposition' in response.headers:
                options['content_disposition'] = response.headers['content-disposition']

            result = codec.decode(data, **options)

        return result


    def _decode_result_error(self, result, response):
        is_error = response.status_code >= 400 and response.status_code <= 599
        if is_error and not isinstance(result, schema.Error):
            default_title = "{} {}".format(response.status_code, response.reason)
            result = self._coerce_to_error(result, default_title = default_title)
        return result

    def _coerce_to_error(self, obj, default_title):
        if isinstance(obj, schema.Document):
            return schema.Error(
                title = obj.title or default_title,
                content = self._coerce_to_error_content(obj)
            )
        elif isinstance(obj, dict):
            return schema.Error(title = default_title, content = obj)
        elif isinstance(obj, list):
            return schema.Error(title = default_title, content = { 'messages': obj })
        elif obj is None:
            return schema.Error(title = default_title)
        return schema.Error(title = default_title, content = { 'message': obj })

    def _coerce_to_error_content(self, node):
        if isinstance(node, (schema.Document, schema.Object)):
            return OrderedDict([
                (key, self._coerce_to_error_content(value))
                for key, value in node.data.items()
            ])
        elif isinstance(node, schema.Array):
            return [
                self._coerce_to_error_content(item)
                for item in node
                if not isinstance(item, schema.Link)
            ]
        return node
