from zimagi.exceptions import ResponseError

from tests.sdk.base import BaseTest


OPENAPI_VERSION = '3.0.3'
DATA_TYPES = [
    'cache',
    'notification',
    'notification_group',
    'notification_failure_group',
    'group',
    'config',
    'task_interval',
    'task_crontab',
    'task_datetime',
    'scheduled_task',
    'log',
    'module',
    'state',
    'user',
    'dataset'
]
DATA_OPS = [
    '/',
    '/csv/',
    '/json/',
    '/values/{field_lookup}/',
    '/count/{field_lookup}/',
    ('/{id}/', '/{name}/'),
]

COMMAND_KEYS = [
    'status',
    'version',
    'user',
    'group',
    'config',
    'state',
    'module',
    'template',
    'schedule',
    'notification',
    'service',
    'db',
    'cache',
    'log',
    'data',
    'send',
    'listen',
    'import',
    'calculate',
    'task',
    'run',
    'destroy'
]


class SchemaTest(BaseTest):

    def test_data_schema(self):
        schema_info = self.data_api.get_schema()

        self.assertEqual(schema_info['openapi'], OPENAPI_VERSION)
        self.assertKeyExists('info', schema_info)
        self.assertKeyExists('components', schema_info)

        self.assertKeyExists('paths', schema_info)
        self.assertKeyExists('/status/', schema_info['paths'])
        self.assertKeyExists('/download/{name}/', schema_info['paths'])

        for data_type in DATA_TYPES:
            for data_op in DATA_OPS:
                if isinstance(data_op, (list, tuple)):
                    path = [ "/{}{}".format(data_type, op) for op in data_op ]
                else:
                    path = "/{}{}".format(data_type, data_op)

                self.assertKeyExists(path, schema_info['paths'])


    def test_data_schema_param(self):
        try:
            self.data_api.list('group', schema = True)

        except ResponseError as e:
            schema_info = e.result
            self.assertEqual(schema_info['operationId'], 'listGroups')
            self.assertEqual(schema_info['description'], '/group/')
            self.assertKeyExists('parameters', schema_info)
            return

        self.fail("API data schema does not trigger response error")


    def test_data_help_param(self):
        try:
            self.data_api.list('group', help = True)

        except ResponseError as e:
            schema_info = e.result
            self.assertEqual(schema_info['detail'], 'API parameter help')
            self.assertKeyExists('parameters', schema_info)
            return

        self.fail("API parameter help does not trigger response error")


    def test_data_wrong_param(self):
        parameter = 'wrong'
        try:
            self.data_api.list('group', **{ parameter: True })

        except ResponseError as e:
            schema_info = e.result
            self.assertEqual(schema_info['detail'], 'Requested filter parameters not found')
            self.assertKeyExists('not_found', schema_info)
            self.assertEqual(schema_info['not_found'][0]['field'], parameter)
            self.assertKeyExists('similar', schema_info['not_found'][0])
            return

        self.fail("API parameter wrong parameter does not trigger response error")


    def test_command_schema(self):
        schema_info = self.command_api.get_schema()
        for command_key in COMMAND_KEYS:
            self.assertKeyExists(command_key, schema_info)
