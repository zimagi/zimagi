from http import cookiejar
from requests.exceptions import ConnectionError

from . import settings, exceptions, utility

import logging
import requests
import urllib
import urllib3


logger = logging.getLogger(__name__)


class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


class BaseTransport(object):

    def __init__(self,
        client = None,
        verify_cert = False,
        options_callback = None,
        request_callback = None,
        response_callback = None
    ):
        self.client = client
        self.verify_cert = verify_cert

        self.options_callback = options_callback
        self.request_callback = request_callback
        self.response_callback = response_callback

        urllib3.disable_warnings()


    def request(self, url, decoders, params = None):
        connection_error_message = "\n".join([
            '',
            'The Zimagi client failed to connect with the server.',
            '',
            'This could indicate the server is down or restarting.',
            'If restarting, retry in a few minutes...'
        ])
        try:
            accept_media_types = []
            for decoder in decoders:
                accept_media_types.extend(decoder.media_types)

            headers = {
                'accept': ", ".join(accept_media_types),
                'user-agent': 'zimagi-python'
            }
            if not params:
                params = {}
            if self.options_callback and callable(self.options_callback):
                self.options_callback(params)

            return self.handle_request(url,
                urllib.parse.urlparse(url).path,
                headers,
                params,
                decoders
            )
        except ConnectionError as error:
            logger.debug("Request {} connection error: {}".format(url, error))
            raise exceptions.ConnectionError(connection_error_message)

    def handle_request(self, url, path, headers, params, decoders):
        raise NotImplementedError("Method handle_request(...) must be overidden in all sub classes")


    def request_page(self, url, headers, params, decoders, encrypted = True, disable_callbacks = False):
        request, response = self._request(url,
            headers = headers,
            params = params,
            encrypted = encrypted,
            disable_callbacks = disable_callbacks
        )
        logger.debug("Page {} request headers: {}".format(url, headers))

        if response.status_code >= 400:
            raise exceptions.ResponseError(
                utility.format_response_error(response, self.client.cipher if encrypted else None)
            )
        return self.decode_message(request, response, decoders,
            decrypt = encrypted,
            disable_callbacks = disable_callbacks
        )


    def _request(self, url, headers = None, params = None, method = 'GET', encrypted = True, stream = False, disable_callbacks = False):
        session = requests.Session()
        session.auth = self.client.auth

        options = { "headers": headers or {} }
        if params:
            parameter_name = 'data' if method == 'POST' else 'params'
            options[parameter_name] = self._encrypt_params(params) if encrypted else params

        request = session.prepare_request(
            requests.Request(method, url, **options)
        )
        settings = session.merge_environment_settings(
            request.url, None, stream, self.verify_cert, None
        )
        settings['timeout'] = None

        if not disable_callbacks and self.request_callback and callable(self.request_callback):
            self.request_callback(request, settings)

        session.cookies.set_policy(BlockAll())
        return (request, session.send(request, **settings))


    def _encrypt_params(self, params):
        if not self.client.cipher:
            return params

        enc_params = {}
        for key, value in params.items():
            enc_params[key] = self.client.cipher.encrypt(value)
        return enc_params


    def decode_message(self, request, response, decoders, message = None, decrypt = True, disable_callbacks = False):
        content = message if message else response.content
        data = None

        if content:
            content_type = response.headers['content-type']
            codec = self._get_decoder(content_type, decoders)

            if decrypt and self.client.cipher:
                content = self.client.cipher.decrypt(content)
                if message is None:
                    response._content = content

            data = codec.decode(content,
                base_url = response.url,
                content_type = content_type
            )
            if not disable_callbacks and self.response_callback and callable(self.response_callback):
                self.response_callback(request, response, data)

        return data

    def _get_decoder(self, content_type, decoders):
        content_type = content_type.split(';')[0].strip().lower()

        for codec in decoders:
            if content_type in codec.media_types:
                return codec

        raise exceptions.ClientError(
            "Unsupported media in Content-Type header '{}'".format(content_type)
        )
