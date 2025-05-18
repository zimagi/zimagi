from django.test import tag
from tests.sdk_python.base import BaseTest
from utility.data import normalize_value


@tag("init", "create")
class CreateTest(BaseTest):
    @tag("create_group")
    def test_group_create(self):
        group_data = {
            "name": "test3",
            "provider_type": "classification",
            "parent": {"name": "test1", "provider_type": "classification"},
            "children": [
                {"name": "test2", "provider_type": "classification"},
                {"name": "test4", "provider_type": "classification", "config": {"something": "True"}},
            ],
            "config_set": [
                {
                    "name": "test1",
                    "value": True,
                    "value_type": "bool",
                    "config": {"first": 1, "second": "2"},
                },
                {"name": "test2", "provider_type": "base", "value": "something", "value_type": "str"},
            ],
        }
        self.assertObjectContains(self.data_api.create("group", **group_data), self._clean_data(group_data))
        for config_name in ["test1", "test2"]:
            self.data_api.delete("config", config_name)

        for group_name in ["test1", "test2", "test3", "test4"]:
            self.data_api.delete("group", group_name)

    def _clean_data(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self._clean_data(value)
        elif isinstance(data, (list, tuple)):
            for index, value in enumerate(data):
                data[index] = self._clean_data(value)
        elif isinstance(data, str):
            data = normalize_value(data)
        return data
