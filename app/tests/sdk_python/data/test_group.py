from tests.sdk_python.data.base import DataBaseTest


DATA_TYPE = 'group'


class GroupTest(DataBaseTest):

    load_types = [ DATA_TYPE ]


    def test_group_list(self):
        count = 20
        response = self.data_api.list(DATA_TYPE)
        self.assertEqual(response.count, count)
        self.assertEqual(len(response.results), count)


    def test_group_update(self):
        config_data = {
            'first': 1,
            'second': 2
        }
        self.data_api.update(DATA_TYPE, 'test__1',
            config = config_data
        )
        self.assertObjectEqual(
            self.data_api.get(DATA_TYPE, 'test__1').config,
            config_data
        )

        objects = self.data_api.json(DATA_TYPE,
            fields = [
                'name',
                'first=config__first'
            ],
            config__first__isnull = False
        )
        self.assertEqual(len(objects), 1)
        self.assertObjectEqual(objects[0], {
            'name': 'test__1',
            'first': 1
        })

