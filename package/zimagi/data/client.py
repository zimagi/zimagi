from .. import settings, utility, client
from .. import codecs as shared_codecs
from . import codecs, transports


class Client(client.BaseAPIClient):

    def __init__(self,
        port = settings.DEFAULT_DATA_PORT,
        verify_cert = settings.DEFAULT_VERIFY_CERT,
        options_callback = None,
        **kwargs
    ):
        super().__init__(
            port = port,
            decoders = [
                codecs.OpenAPIJSONCodec(),  # application/vnd.oai.openapi+json
                shared_codecs.JSONCodec()   # application/json
            ],
            **kwargs
        )
        self.transport = transports.DataHTTPSTransport(
            client = self,
            verify_cert = verify_cert,
            options_callback = options_callback
        )
        if not self.get_status().encryption:
            self.cipher = None


    def get_status(self):
        if not getattr(self, '_status', None):
            status_url = "/".join([ self.base_url.rstrip('/'), 'status' ])

            def processor():
                return self._request(status_url)

            self._status = utility.wrap_api_call('data_status', status_url, processor)
        return self._status


    def execute(self, path, options = None):
        url = "/".join([ self.base_url.rstrip('/'), path ])

        if not options:
            options = {}
        options = utility.format_options(options)

        def processor():
            return self._request(url, options)

        return utility.wrap_api_call('data', path, processor, options)


    def _execute_type_operation(self, data_type, op, options):
        if op is None:
            return self.execute(data_type, options)
        return self.execute("{}/{}".format(data_type, op), options)

    def _execute_key_operation(self, data_type, op, key, options):
        if op is None:
            return self.execute("{}/{}".format(data_type, key), options)
        return self.execute("{}/{}/{}".format(data_type, key, op), options)

    def _execute_field_operation(self, data_type, op, field_name, options):
        return self.execute("{}/{}/{}".format(data_type, op, field_name), options)


    def list(self, data_type, options = None):
        return self._execute_type_operation(data_type, None, options)

    def json(self, data_type, options = None):
        return self._execute_type_operation(data_type, 'json', options)

    def csv(self, data_type, options = None):
        return self._execute_type_operation(data_type, 'csv', options)


    def get(self, data_type, key, options = None):
        return self._execute_key_operation(data_type, None, key, options)


    def values(self, data_type, field_name, options = None):
        return self._execute_field_operation(data_type, 'values', field_name, options)

    def count(self, data_type, field_name, options = None):
        return self._execute_field_operation(data_type, 'count', field_name, options)


    def download(self, dataset_name):
        return self.execute("download/{}".format(dataset_name))
