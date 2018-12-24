
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

import requests
import itypes
import urllib3


class CommandHTTPSTransport(BaseTransport):

    schemes = ['https']


    def __init__(self, headers = None, auth = None, message_callback = None):
        self._auth = auth

        if headers:
            headers = {key.lower(): value for key, value in headers.items()}
        
        self._headers = itypes.Dict(headers or {})
        self._message_callback = message_callback

        urllib3.disable_warnings()
    

    def init_session(self):
        session = requests.Session()

        if self._auth is not None:
            session.auth = self._auth
        
        if not getattr(session.auth, 'allow_cookies', False):
            session.cookies.set_policy(BlockAll())

        return session        


    def _build_get_request(self, session, url, headers, params):
        opts = { "headers": headers or {} }

        if params.query:
            opts['params'] = params.query

        request = requests.Request('GET', url, **opts)
        return session.prepare_request(request)

    def _build_post_request(self, session, url, headers, params):
        opts = { "headers": headers or {} }

        if params.data:
            opts['data'] = params.data
    
        request = requests.Request('POST', url, **opts)
        return session.prepare_request(request)


    def transition(self, link, decoders, params = None, link_ancestors = None, force_codec = None):
        encoding = link.encoding if link.encoding else 'application/x-www-form-urlencoded'
        params = _get_params(link.action.upper(), encoding, link.fields, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders)
        headers.update(self._headers)
                
        if link.action == 'get':
            result = self.request_page(url, headers, params, decoders)

            if isinstance(result, Document) and link_ancestors:
                result = _handle_inplace_replacements(result, link, link_ancestors)

            if isinstance(result, Error):
                raise exceptions.ErrorMessage(result)

            return result
        else:
            return self.request_stream(url, headers, params, decoders)


    def request_page(self, url, headers, params, decoders):
        session = self.init_session()
        request = self._build_get_request(session, url, headers, params)
        settings = session.merge_environment_settings(
            request.url, None, None, False, None
        )
        response = session.send(request, **settings)
        return _decode_result(response, decoders)

    def request_stream(self, url, headers, params, decoders):
        session = self.init_session()
        request = self._build_post_request(session, url, headers, params)
        settings = session.merge_environment_settings(
            request.url, None, True, False, None
        )
        response = session.send(request, **settings)
        result = []

        for line in response.iter_lines():
            data = self._decode_message(response, line, decoders)
            result.append(data)

            if self._message_callback and callable(self._message_callback):
                self._message_callback(data)

        return result


    def _decode_message(self, response, data, decoders):
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
        else:
            result = None

        is_error = response.status_code >= 400 and response.status_code <= 599
        if is_error and not isinstance(result, Error):
            default_title = '%d %s' % (response.status_code, response.reason)
            result = _coerce_to_error(result, default_title = default_title)

        return result
