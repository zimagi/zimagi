from .. import settings, utility, client, exceptions
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
        self.schema = self.get_schema()
        self._id_fields = {}
        self._key_fields = {}

        if not self.get_status().encryption:
            self.cipher = None


    def get_paths(self):
        return self.schema['paths']

    def get_id_field(self, data_type):
        if data_type not in self._id_fields:
            for parameter in self.schema['paths']["/{}/".format(data_type)]['get']['parameters']:
                if 'x-id' in parameter['schema']:
                    self._id_fields[data_type] = parameter['name']
                    break
        return self._id_fields[data_type]

    def get_key_field(self, data_type):
        if data_type not in self._key_fields:
            for parameter in self.schema['paths']["/{}/".format(data_type)]['get']['parameters']:
                if 'x-key' in parameter['schema']:
                    self._key_fields[data_type] = parameter['name']
                    break
        return self._key_fields[data_type]



    def _execute(self, method, path, options = None):
        url = "/".join([ self.base_url.rstrip('/'), path ])

        if not options:
            options = {}
        options = utility.format_options(options)

        def processor():
            return self._request(method, url, options)

        return utility.wrap_api_call('data', path, processor, options)


    def _execute_type_operation(self, method, data_type, op, options):
        if op is None:
            return self._execute(method, data_type, options)
        return self._execute(method, "{}/{}".format(data_type, op), options)

    def _execute_key_operation(self, method, data_type, op, key, options):
        if op is None:
            return self._execute(method, "{}/{}".format(data_type, key), options)
        return self._execute(method, "{}/{}/{}".format(data_type, key, op), options)

    def _execute_field_operation(self, method, data_type, op, field_name, options):
        return self._execute(method, "{}/{}/{}".format(data_type, op, field_name), options)


    def create(self, data_type, **fields):
        return self._execute_type_operation('POST', data_type, None, fields)

    def update(self, data_type, id, **fields):
        return self._execute_key_operation('PUT', data_type, None, id, fields)

    def delete(self, data_type, id):
        return self._execute_key_operation('DELETE', data_type, None, id, {})

    def get(self, data_type, id, **options):
        return self._execute_key_operation('GET', data_type, None, id, options)

    def get_by_key(self, data_type, key, **options):
        options[self.get_key_field(data_type)] = key
        results = self._execute_type_operation('GET', data_type, None, options)

        if results.count == 0:
            raise exceptions.ResponseError("Instance {} {}: not found".format(data_type, key))
        elif results.count > 1:
            raise exceptions.ResponseError("Instance {} {}: too many found".format(data_type, key))

        return results.results[0]


    def list(self, data_type, **options):
        return self._execute_type_operation('GET', data_type, None, options)

    def json(self, data_type, **options):
        return self._execute_type_operation('GET', data_type, 'json', options)

    def csv(self, data_type, **options):
        return self._execute_type_operation('GET', data_type, 'csv', options)


    def values(self, data_type, field_name, **options):
        return self._execute_field_operation('GET', data_type, 'values', field_name, options)

    def count(self, data_type, field_name, **options):
        return self._execute_field_operation('GET', data_type, 'count', field_name, options)


    def download(self, dataset_name):
        return self._execute('GET', "download/{}".format(dataset_name))
