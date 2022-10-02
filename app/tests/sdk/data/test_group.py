from tests.sdk.data.base import DataBaseTest


DATA_TYPE = 'group'


class GroupTest(DataBaseTest):

    load_types = [ DATA_TYPE ]


    def test_group_list(self):
        count = 20
        response = self.data_api.list(DATA_TYPE)
        self.assertEqual(response.count, count)
        self.assertEqual(len(response.results), count)
