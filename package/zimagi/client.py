from . import settings, exceptions, utility, encryption, auth


class BaseAPIClient(object):

    def __init__(self,
        host = settings.DEFAULT_HOST,
        port = None,
        user = settings.DEFAULT_USER,
        token = settings.DEFAULT_TOKEN,
        encryption_key = None,
        decoders = None
    ):
        self.host = host
        self.port = port

        if self.port is None:
            raise exceptions.ClientError('Cannot instantiate BaseAPIClient directly')

        self.base_url = utility.get_service_url(host, port)
        self.cipher = encryption.Cipher.get(encryption_key) if encryption_key else None
        self.transport = None
        self.decoders = decoders

        self.auth = auth.ClientTokenAuthentication(
            client = self,
            user = user,
            token = token
        )

    def _request(self, method, url, params = None):
        if not self.transport:
            raise exceptions.ClientError('Zimagi API client transport not defined')

        return self.transport.request(method, url,
            self.decoders,
            params = params,
            tries = settings.CONNECTION_RETRIES,
            wait = settings.CONNECTION_RETRY_WAIT
        )


    def get_status(self):
        if not getattr(self, '_status', None):
            status_url = "/".join([ self.base_url.rstrip('/'), 'status' ])

            def processor():
                return self._request('GET', status_url)

            self._status = utility.wrap_api_call('status', status_url, processor)
        return self._status

    def get_schema(self):
        if not getattr(self, '_schema', None):

            def processor():
                return self._request('GET', self.base_url)

            self._schema = utility.wrap_api_call('schema', self.base_url, processor)
        return self._schema
