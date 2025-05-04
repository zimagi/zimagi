import logging

from . import auth, encryption, exceptions, settings, utility


class BaseAPIClient:
    def __init__(
        self,
        protocol="https",
        host=settings.DEFAULT_HOST,
        port=None,
        user=settings.DEFAULT_USER,
        token=settings.DEFAULT_TOKEN,
        encryption_key=None,
        decoders=None,
    ):
        self.host = host
        self.port = port

        if self.port is None:
            raise exceptions.ClientError("Cannot instantiate BaseAPIClient directly")

        log_level = getattr(logging, settings.LOG_LEVEL.upper(), None)
        if not isinstance(log_level, int):
            raise ValueError("Invalid Zimagi package log level specified")

        logging.basicConfig(level=log_level)

        self.base_url = utility.get_service_url(protocol, host, port)
        self.cipher = encryption.Cipher.get(encryption_key) if encryption_key else None
        self.transport = None
        self.decoders = decoders

        self.auth = auth.ClientTokenAuthentication(client=self, user=user, token=token)

    def _request(self, method, url, params=None, validate_callback=None):
        if not self.transport:
            raise exceptions.ClientError("Zimagi API client transport not defined")

        return self.transport.request(
            method,
            url,
            self.decoders,
            params=params,
            tries=settings.CONNECTION_RETRIES,
            wait=settings.CONNECTION_RETRY_WAIT,
            validate_callback=validate_callback,
        )

    def get_status(self):
        if not getattr(self, "_status", None):
            status_url = "/".join([self.base_url.rstrip("/"), "status"])

            def processor():
                return self._request("GET", status_url)

            self._status = utility.wrap_api_call("status", status_url, processor)
        return self._status

    def get_schema(self):
        if not getattr(self, "_schema", None):

            def schema_generator():
                def processor():
                    return self._request("GET", self.base_url)

                return utility.wrap_api_call("schema", self.base_url, processor)

            self._schema = utility.cache_data(
                f"{self.host}.{self.port}", schema_generator, cache_lifetime=settings.CACHE_LIFETIME
            )

        return self._schema
