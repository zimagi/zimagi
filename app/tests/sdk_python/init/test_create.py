from tests.sdk_python.base import BaseTest


class CreateTest(BaseTest):

    def test_group_create(self):
        group_data = {
            'name': 'test3',
            'provider_type': 'classification',
            'parent': {
                'name': 'test1',
                'provider_type': 'classification'
            },
            'children': [
                {
                    'name': 'test2',
                    'provider_type': 'classification'
                },
                {
                    'name': 'test4',
                    'provider_type': 'classification',
                    'config': {
                        'something': True
                    }
                }
            ],
            'config_set': [
                {
                    'name': 'test1',
                    'value': True,
                    'value_type': 'bool',
                    'config': {
                        'first': 1,
                        'second': 2
                    }
                },
                {
                    'name': 'test2',
                    'provider_type': 'base',
                    'value': 'something',
                    'value_type': 'str'
                }
            ]
        }
        self.assertObjectEqual(
            group_data,
            self.data_api.create('group', **group_data)
        )
        for config_name in ['test1', 'test2']:
            self.data_api.delete('config', config_name)

        for group_name in ['test1', 'test2', 'test3', 'test4']:
            self.data_api.delete('group', group_name)
