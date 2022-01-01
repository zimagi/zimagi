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


    def _request(self, url, params = None):
        if not self.transport:
            raise exceptions.ClientError('Zimagi API client transport not defined')

        return self.transport.request(url, self.decoders, params = params)
