from django.test import tag
from tests.sdk_python.data.base import DataBaseTest

DATA_TYPE = "group"


@tag("data", "group")
class GroupTest(DataBaseTest):
    load_types = [DATA_TYPE]

    @tag("group_list")
    def test_group_list(self):
        count = 19
        response = self.data_api.list(DATA_TYPE)
        self.assertEqual(response.count, count)
        self.assertEqual(len(response.results), count)

    @tag("group_update")
    def test_group_update(self):
        config_data = {"first": 1, "second": 2}
        self.data_api.update(DATA_TYPE, "test__1", config=config_data)
        self.assertObjectEqual(self.data_api.get(DATA_TYPE, "test__1").config, config_data)

        objects = self.data_api.json(DATA_TYPE, fields=["name", "first=config__first"], config__first__isnull=False)
        self.assertEqual(len(objects), 1)
        self.assertObjectEqual(objects[0], {"name": "test__1", "first": 1})

    @tag("group_csv")
    def test_group_csv(self):
        data = self.data_api.csv(
            DATA_TYPE,
            fields=["name", "provider=provider_type", "created", "updated", "parent=parent__name", "user=user__name"],
        )
        rows, columns = data.shape
        self.assertEqual(rows, 19)
        self.assertEqual(columns, 6)
        self.assertObjectEqual(list(data.columns), ["name", "created", "updated", "parent", "user", "provider"])
