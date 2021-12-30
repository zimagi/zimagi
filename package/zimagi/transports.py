from http import cookiejar

from . import exceptions, utility, encryption

import logging
import requests
import urllib3
import uritemplate


logger = logging.getLogger(__name__)


def validate_param(param_value, allow_list = True):
    if isinstance(param_value, str):
        return param_value
    elif isinstance(param_value, bool) or param_value is None:
        return { True: 'true', False: 'false', None: '' }[param_value]
    elif isinstance(param_value, (int, float)):
        return str(param_value)
    elif allow_list and isinstance(param_value, (list, tuple)):
        return [
            validate_param(item, allow_list = False)
            for item in param_value
        ]
    raise exceptions.ParameterError("Must be a primitive type.")

def validate_path_param(param_value):
    value = validate_param(param_value, allow_list = False)
    if not value:
        raise exceptions.ParameterError("Parameter: May not be empty.")
    return value

def validate_query_param(param_value):
    return validate_param(param_value)

def validate_json_data(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    elif isinstance(value, (list, tuple)):
        return [ validate_json_data(item) for item in value ]
    elif isinstance(value, dict):
        return {
            str(item_key): validate_json_data(item_val)
            for item_key, item_val in value.items()
        }
    raise exceptions.ParameterError('Must be a JSON primitive.')

def validate_form_object(value):
    if not isinstance(value, dict):
        raise exceptions.ParameterError('Must be an object.')
    return {
        str(item_key): validate_param(item_val)
        for item_key, item_val in value.items()
    }

def validate_body_param(value, encoding):
    if encoding == 'application/json':
        return validate_json_data(value)
    elif encoding == 'multipart/form-data':
        return validate_form_object(value)
    elif encoding == 'application/x-www-form-urlencoded':
        return validate_form_object(value)

    raise exceptions.ParameterError("Unsupported encoding '{}' for outgoing request.".format(encoding))

def validate_form_param(value, encoding):
    if encoding == 'application/json':
        return validate_json_data(value)
    elif encoding == 'multipart/form-data':
        return validate_param(value)
    elif encoding == 'application/x-www-form-urlencoded':
        return validate_param(value)

    raise exceptions.ParameterError("Unsupported encoding '{}' for outgoing request.".format(encoding))


class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


class Parameters(object):

    def __init__(self, path = None, query = None, data = None):
        self.path = path
        self.query = query
        self.data = data


class BaseTransport(object):

    schemes = ['https']


    def __init__(self,
        headers = None,
        auth = None,
        encryption_key = None
    ):
        self._auth = auth
        self._cipher = encryption.Cipher.get(encryption_key)

        if headers:
            headers = { key.lower(): value for key, value in headers.items() }

        self._headers = headers or {}

        urllib3.disable_warnings()


    def init_session(self):
        session = requests.Session()

        if self._auth is not None:
            session.auth = self._auth

        session.cookies.set_policy(BlockAll())
        return session


    def transition(self, link, decoders, params = None):
        raise NotImplementedError("Method transmission(...) must be overidden in all sub classes")


    def get_url(self, url, path_params):
        if path_params:
            return uritemplate.expand(url, path_params)
        return url

    def get_headers(self, url, decoders):
        accept_media_types = decoders[0].media_types
        if '*/*' not in accept_media_types:
            accept_media_types.append('*/*')

        headers = {
            'accept': ', '.join(accept_media_types),
            'user-agent': 'zimagi-python'
        }
        return headers

    def get_params(self, link, params = None):
        method = link.action.upper()
        encoding = link.encoding
        fields = link.fields

        if params is None:
            return Parameters({}, {}, {})

        field_map = { field.name: field for field in fields }

        path = {}
        query = {}
        data = {}
        errors = {}

        seen_body = False

        for key, value in params.items():
            if key not in field_map or not field_map[key].location:
                location = 'query' if method in ('GET',) else 'form'
            else:
                location = field_map[key].location

            if location == 'form' and encoding == 'application/octet-stream':
                location = 'body'
            try:
                if location == 'path':
                    path[key] = validate_path_param(value)
                elif location == 'query':
                    query[key] = validate_query_param(value)
                elif location == 'body':
                    data = validate_body_param(value, encoding = encoding)
                    seen_body = True
                elif location == 'form':
                    if not seen_body:
                        data[key] = validate_form_param(value, encoding = encoding)

            except exceptions.ParameterError as exc:
                errors[key] = str(exc)
        if errors:
            raise exceptions.ParameterError(errors)

        return Parameters(path, query, data)



    def request_page(self, url, headers, params, decoders, timeout = 30):
        session = self.init_session()
        request = self._build_get_request(session, url, headers, params)
        settings = session.merge_environment_settings(
            request.url, None, None, False, None
        )
        settings['timeout'] = timeout

        logger.debug("Page {} request headers: {}".format(request.url, request.headers))

        response = session.send(request, **settings)
        if response.status_code >= 500:
            raise exceptions.CommandResponseError(
                utility.format_response_error(response)
            )
        return self._decode_result(response, decoders)


    def _build_get_request(self, session, url, headers, params):
        opts = { "headers": headers or {} }

        if params.query:
            opts['params'] = self._encrypt_params(params.query)

        return session.prepare_request(
            requests.Request('GET', url, **opts)
        )

    def _build_post_request(self, session, url, headers, params):
        opts = { "headers": headers or {} }

        if params.data:
            opts['data'] = self._encrypt_params(params.data)

        return session.prepare_request(
            requests.Request('POST', url, **opts)
        )


    def _encrypt_params(self, params):
        enc_params = {}
        for key, value in params.items():
            enc_params[key] = self._cipher.encrypt(value)

        return enc_params


    def _negotiate_decoder(self, decoders, content_type = None):
        if content_type is None:
            return decoders[0]

        content_type = content_type.split(';')[0].strip().lower()
        main_type = content_type.split('/')[0] + '/*'
        wildcard_type = '*/*'

        for codec in decoders:
            for media_type in codec.media_types:
                if media_type in (content_type, main_type, wildcard_type):
                    return codec

        raise exceptions.CodecError(
            "Unsupported media in Content-Type header '{}'".format(content_type)
        )


    def _decode_result(self, response, decoders):
        result = None

        if response.content:
            content_type = response.headers.get('content-type')
            codec = self._negotiate_decoder(decoders, content_type)

            options = {
                'base_url': response.url
            }
            if 'content-type' in response.headers:
                options['content_type'] = response.headers['content-type']
            if 'content-disposition' in response.headers:
                options['content_disposition'] = response.headers['content-disposition']

            result = codec.decode(response.content, **options)

        return self._decode_result_error(result, response)

    def _decode_result_error(self, result, response):
        # Override in subclass if needed
        return result
