from tests.sdk_python.base import BaseTest
from utility.data import dump_json

from zimagi.exceptions import ResponseError


class DataBaseTest(BaseTest):
    load_types = []

    @classmethod
    def setup(cls):
        errors = []

        for type in cls.load_types:
            key_field = cls.data_api.get_key_field(type)
            data = cls._load_data(type)

            setattr(cls, f"{type}_data", data)
            setattr(cls, f"{type}_count", len(data.keys()))

            for key, fields in data.items():
                fields[key_field] = key
                try:
                    cls.data_api.create(type, **fields)
                except ResponseError as e:
                    errors.append(f"{type}: {e}\nprovided: {dump_json(fields, indent=2)}")

                if not errors:
                    cls.create_data(type, key, fields)

        if errors:
            raise ResponseError("\n\n".join(errors))

    @classmethod
    def create_data(cls, type, key, fields):
        # Override in subclass if needed
        pass

    @classmethod
    def tear_down(cls):
        errors = []

        for type in reversed(cls.load_types):
            id_field = cls.data_api.get_id_field(type)
            data = getattr(cls, f"{type}_data")

            for key in reversed(list(data.keys())):
                instance = cls.data_api.get_by_key(type, key, **data[key])
                id = instance[id_field]

                try:
                    cls.data_api.delete(type, id)
                except ResponseError as e:
                    errors.append(f"{type}: {e}")
                if not errors:
                    cls.clear_data(type, id, key, data[key])

        if errors:
            raise ResponseError("\n\n".join(errors))

    @classmethod
    def clear_data(cls, type, id, key, fields):
        # Override in subclass if needed
        pass
