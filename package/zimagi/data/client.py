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
                codecs.CSVCodec(),          # text/csv
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

        self.schema = self.get_schema()
        self._data_info = {}


    def get_paths(self):
        return self.schema['paths']

    def get_path(self, path):
        return self.get_paths()["/{}/".format(path.strip('/'))]


    def _set_data_info(self, data_type):
        if data_type not in self._data_info:
            self._data_info[data_type] = self.get_path(data_type).get('x-data', {})

    def get_id_field(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('id', None)

    def get_key_field(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('key', None)

    def get_unique_fields(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('unique', [])

    def get_dynamic_fields(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('dynamic', [])

    def get_atomic_fields(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('atomic', [])

    def get_scope_fields(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('scope', {})

    def get_relation_fields(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('relations', {})

    def get_reverse_fields(self, data_type):
        self._set_data_info(data_type)
        return self._data_info[data_type].get('reverse', {})


    def set_scope(self, data_type, values, parents = None):
        scope_fields = self.get_scope_fields(data_type)
        filters = {}

        if parents is None:
            parents = []

        for scope_field, scope_type in scope_fields.items():
            scope_parents = [ *parents, scope_field ]
            scope_field = "__".join(scope_parents)

            if scope_field in values:
                scope_key = self.get_key_field(scope_type)
                filters["{}__{}".format(scope_field, scope_key)] = values[scope_field]
                filters.update(self.set_scope(scope_type, values, scope_parents))

        return filters


    def _execute(self, method, path, options = None):
        url = "{}/".format("/".join([ self.base_url.rstrip('/'), path ]).rstrip('/'))

        if not options:
            options = {}
        if method == 'GET':
            options = utility.format_options(method, options)

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
        results = self._execute_type_operation('GET', data_type, None, {
            self.get_key_field(data_type): key,
            **self.set_scope(data_type, options)
        })
        if results.count is None:
            raise exceptions.ResponseError("Instance {} {}: {}".format(data_type, key, results))
        elif results.count == 0:
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
