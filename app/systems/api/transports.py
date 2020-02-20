
from requests.exceptions import ConnectionError
from coreapi import exceptions, utils
from coreapi.transports.base import BaseTransport
from coreapi.document import Document, Error
from coreapi.transports.http import (
    BlockAll,
    _get_params,
    _get_url,
    _get_headers,
    _decode_result,
    _handle_inplace_replacements,
    _coerce_to_error
)

from django.core.management.base import CommandError
from utility.terminal import TerminalMixin
from utility.encryption import Cipher

import logging
import requests
import itypes
import urllib3
import json


logger = logging.getLogger(__name__)


class CommandHTTPSTransport(TerminalMixin, BaseTransport):

    schemes = ['https']


    def __init__(self, headers = None, auth = None, params_callback = None, message_callback = None):
        self._auth = auth

        if headers:
            headers = {key.lower(): value for key, value in headers.items()}

        self._headers = itypes.Dict(headers or {})
        self._params_callback = params_callback
        self._message_callback = message_callback

        urllib3.disable_warnings()


    def init_session(self, require_auth = True):
        session = requests.Session()

        if require_auth and self._auth is not None:
            session.auth = self._auth

        if not getattr(session.auth, 'allow_cookies', False):
            session.cookies.set_policy(BlockAll())

        return session


    def _encrypt_params(self, params):
        cipher = Cipher.get('params')
        enc_params = {}

        for key, value in params.items():
            key = cipher.encrypt(key)
            value = cipher.encrypt(value)
            enc_params[key] = value

        return enc_params


    def _build_get_request(self, session, url, headers, params):
        opts = { "headers": headers or {} }

        if params.query:
            opts['params'] = self._encrypt_params(params.query)

        request = requests.Request('GET', url, **opts)
        return session.prepare_request(request)

    def _build_post_request(self, session, url, headers, params):
        opts = { "headers": headers or {} }

        if params.data:
            opts['data'] = self._encrypt_params(params.data)

        request = requests.Request('POST', url, **opts)
        return session.prepare_request(request)


    def transition(self, link, decoders, params = None, link_ancestors = None, force_codec = None):
        encoding = link.encoding if link.encoding else 'application/x-www-form-urlencoded'
        params = _get_params(link.action.upper(), encoding, link.fields, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders)
        headers.update(self._headers)

        connection_error_message = self.error_color("\n".join([
            '',
            'The MCMI client failed to connect with the server.',
            '',
            'This could indicate the server is down or restarting.',
            'If restarting, retry in a few minutes...'
        ]))
        if link.action == 'get':
            try:
                result = self.request_page(url, headers, params, decoders)

                if isinstance(result, Document) and link_ancestors:
                    result = _handle_inplace_replacements(result, link, link_ancestors)

                if isinstance(result, Error):
                    raise exceptions.ErrorMessage(result)

                return result

            except ConnectionError as e:
                self.print(connection_error_message)
                raise CommandError()
        else:
            if self._params_callback and callable(self._params_callback):
                self._params_callback(params)

            try:
                return self.request_stream(url, headers, params, decoders)
            except ConnectionError as e:
                self.print(connection_error_message)
                raise CommandError()


    def request_page(self, url, headers, params, decoders):
        session = self.init_session(False) # GET
        request = self._build_get_request(session, url, headers, params)
        settings = session.merge_environment_settings(
            request.url, None, None, False, None
        )
        settings['timeout'] = 30

        response = session.send(request, **settings)
        return _decode_result(response, decoders)

    def request_stream(self, url, headers, params, decoders):
        session = self.init_session(True) # POST
        request = self._build_post_request(session, url, headers, params)
        settings = session.merge_environment_settings(
            request.url, None, True, False, None
        )
        response = session.send(request, **settings)
        result = []

        if response.status_code >= 400:
            message = "Error {}: {}".format(response.status_code, response.reason)
            self.print(self.error_color(message))
            try:
                self.print(self.error_color(json.loads(response.text)['detail']))
            except Exception:
                self.print(self.error_color(response.text))
            raise CommandError()

        try:
            for line in response.iter_lines():
                data = self._decode_message(response, line, decoders)

                if self._message_callback and callable(self._message_callback):
                    self._message_callback(data)

                result.append(data)

        except Exception as e:
            self.print(self.error_color("Remote command failed for {}: {}".format(url, params)))
            raise e

        return result


    def _decode_message(self, response, data, decoders):
        result = None

        if data:
            content_type = response.headers.get('content-type')
            codec = utils.negotiate_decoder(decoders, content_type)

            options = {
                'base_url': response.url
            }
            if 'content-type' in response.headers:
                options['content_type'] = response.headers['content-type']
            if 'content-disposition' in response.headers:
                options['content_disposition'] = response.headers['content-disposition']

            result = codec.load(data, **options)

        return result
