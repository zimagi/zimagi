from openapi_core.validation.request.validators import RequestValidator

from .. import utility, client, auth
from .. import codecs as shared_codecs
from . import codecs, transports


class Client(client.BaseAPIClient):

    def __init__(self,
        token,
        user = 'admin',
        host = 'localhost',
        port = 5123,
        encryption_key = None
    ):
        super().__init__(
            host = host,
            port = port,
            transports = [
                transports.DataHTTPSTransport(
                    auth = auth.ClientTokenAuthentication(
                        user = user,
                        token = token,
                        encryption_key = encryption_key
                    ),
                    encryption_key = encryption_key
                ) # https only
            ],
            decoders = [
                codecs.OpenAPIJSONCodec(),  # application/vnd.oai.openapi+json
                shared_codecs.JSONCodec()   # application/json
            ]
        )
        self.schema = self._get_schema()
        self.data_types = self._get_data_types()
        self.validator = RequestValidator(self.schema)


    def _get_schema(self):

        def processor():
            return self._get(self.base_url)

        return utility.wrap_api_call('data_schema', self.base_url, processor)


    def _get_data_types(self):
        data_types = {}

        return data_types

    def get_options(self, data_type):
        options = {}

        return options


    def execute(self, url, options):

        def processor():
            return self._get(url, options)

        return utility.wrap_api_call('data', url, processor)


    def _execute_type_operation(self, data_type, op, options):
        return self.execute("{}{}/{}".format(self.base_url, data_type, op), options)

    def _execute_key_operation(self, data_type, op, key, options):
        return self.execute("{}{}/{}/{}".format(self.base_url, data_type, key, op), options)

    def _execute_field_operation(self, data_type, op, field_name, options):
        return self.execute("{}{}/{}/{}".format(self.base_url, data_type, op, field_name), options)


    def list(self, data_type, options):
        return self._execute_type_operation(data_type, '', options)

    def get(self, data_type, key, options):
        return self._execute_key_operation(data_type, '', key, options)

    def values(self, data_type, field_name, options):
        return self._execute_field_operation(data_type, 'values', field_name, options)

    def count(self, data_type, field_name, options):
        return self._execute_field_operation(data_type, 'count', field_name, options)

    def download(self, dataset_name):
        return self.execute("download/{}".format(dataset_name))
