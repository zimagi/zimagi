
from coreapi import exceptions, transports, utils
from coreapi.document import Document, Error
from coreapi.transports.http import (
    _get_method,
    _get_encoding,
    _get_params,
    _get_url,
    _get_headers,
    _decode_result,
    _handle_inplace_replacements,
    _coerce_to_error
)

import requests


class CommandHTTPTransport(transports.HTTPTransport):

    def __init__(self, headers = None, auth = None, message_callback = None):
        super().__init__(
            headers = headers, 
            auth = auth
        )
        self._message_callback = message_callback


    def _build_get_request(self, url, headers, params):
        opts = { "headers": headers or {} }

        if params.query:
            opts['params'] = params.query

        request = requests.Request('GET', url, **opts)
        return self._session.prepare_request(request)

    def _build_post_request(self, url, headers, params):
        opts = { "headers": headers or {} }

        if params.data:
            opts['data'] = params.data
    
        request = requests.Request('POST', url, **opts)
        return self._session.prepare_request(request)


    def transition(self, link, decoders, params = None, link_ancestors = None, force_codec = None):
        method = _get_method(link.action)
        encoding = _get_encoding(link.encoding)
        params = _get_params(method, encoding, link.fields, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders)
        headers.update(self.headers)
                
        if link.action == 'get':
            request = self._build_get_request(url, headers, params)
            return self.transition_page(link, link_ancestors, request, decoders)
        else:
            # all post requests
            request = self._build_post_request(url, headers, params)
            return self.transition_stream(link, link_ancestors, request, decoders)


    def transition_page(self, link, link_ancestors, request, decoders):
        settings = self._session.merge_environment_settings(
            request.url, None, None, 
            /etc/ssl/certs/cenv-ca.crt, 
            (/etc/ssl/certs/cenv.crt, /etc/ssl/private/cenv.key)
        )
        response = self._session.send(request, **settings)
        result = _decode_result(response, decoders)

        if isinstance(result, Document) and link_ancestors:
            result = _handle_inplace_replacements(result, link, link_ancestors)

        if isinstance(result, Error):
            raise exceptions.ErrorMessage(result)

        return result

    def transition_stream(self, link, link_ancestors, request, decoders):
        settings = self._session.merge_environment_settings(
            request.url, None, True, 
            /etc/ssl/certs/cenv-ca.crt, 
            (/etc/ssl/certs/cenv.crt, /etc/ssl/private/cenv.key)
        )
        response = self._session.send(request, **settings)
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
