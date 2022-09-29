from tests.sdk.data.base import DataBaseTest


DATA_TYPE = 'group'


class GroupTest(DataBaseTest):

    load_types = [ DATA_TYPE ]


    # def test_group_list(self):
    #     print(self.group_data)
    #     print(self.data_api.list(DATA_TYPE).results)
