from tests.sdk.data import DataTest


DATA_TYPE = 'group'


class GroupTest(DataTest):

    load_types = [ DATA_TYPE ]


    def test_group_list(self):
        print(self.group_data)
        print(self.data_api.list(DATA_TYPE).results)
