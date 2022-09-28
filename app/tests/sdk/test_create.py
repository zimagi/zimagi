from tests.sdk.base import BaseTest


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
            ]
        }
        group = self.data_api.create('group', **group_data)
        print(group)

        for group_name in ['test1', 'test2', 'test3', 'test4']:
            self.data_api.delete('group', group_name)
