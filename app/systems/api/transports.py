
from coreapi import exceptions, transports, utils
from coreapi.document import Document, Error
from coreapi.transports.http import (
    _get_method,
    _get_encoding,
    _get_params,
    _get_url,
    _get_headers,
    _build_http_request,
    _decode_result,
    _handle_inplace_replacements
)


def _decode_stream_result(response, data, decoders, force_codec = False):
    if data:
        if force_codec:
            codec = decoders[0]
        else:
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


class StreamingHTTPTransport(transports.HTTPTransport):

    def __init__(self, credentials = None, headers = None, auth = None, session = None, message_callback = None):
        super().__init__(
            credentials = credentials, 
            headers = headers, 
            auth = auth, 
            session = session
        )
        self._message_callback = message_callback


    def transition(self, link, decoders, params = None, link_ancestors = None, force_codec = False):
        method = _get_method(link.action)
        encoding = _get_encoding(link.encoding)
        params = _get_params(method, encoding, link.fields, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders)
        headers.update(self.headers)

        request = _build_http_request(self._session, url, method, headers, encoding, params)
        
        if link.action == 'get':
            return self.transition_schema(link, link_ancestors, request, decoders, force_codec)
        else:
            return self.transition_stream(link, link_ancestors, request, decoders, force_codec)


    def transition_schema(self, link, link_ancestors, request, decoders, force_codec):
        settings = self._session.merge_environment_settings(request.url, None, None, None, None)
        response = self._session.send(request, **settings)
        result = _decode_result(response, decoders, force_codec)

        if isinstance(result, Document) and link_ancestors:
            result = _handle_inplace_replacements(result, link, link_ancestors)

        if isinstance(result, Error):
            raise exceptions.ErrorMessage(result)

        return result

    def transition_stream(self, link, link_ancestors, request, decoders, force_codec):
        settings = self._session.merge_environment_settings(request.url, None, True, None, None)
        response = self._session.send(request, **settings)
        result = []

        for line in response.iter_lines():
            data = _decode_stream_result(response, line, decoders, force_codec)
            result.append(data)

            if self._message_callback and callable(self._message_callback):
                self._message_callback(data)

        return result
