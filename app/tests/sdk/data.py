from .base import BaseTest


class DataTest(BaseTest):

    load_types = []


    @classmethod
    def setup(cls):
        for type in cls.load_types:
            key_field = cls.data_api.get_key_field(type)
            data = cls._load_data(type)

            setattr(cls, "{}_data".format(type), data)
            setattr(cls, "{}_count".format(type), len(data.keys()))

            for key, fields in data.items():
                fields[key_field] = key
                # cls.data_api.create(type, **fields)
                cls.create_data(type, key, fields)

    @classmethod
    def create_data(cls, type, key, fields):
        # Override in subclass if needed
        pass


    @classmethod
    def tear_down(cls):
        for type in reversed(cls.load_types):
            id_field = cls.data_api.get_id_field(type)
            data = getattr(cls, "{}_data".format(type))
            for key in reversed(list(data.keys())):
                # instance = cls.data_api.get_by_key(type, key)
                # id = instance[id_field]

                # cls.data_api.delete(type, id)
                cls.clear_data(type, id, key, data[key])

    @classmethod
    def clear_data(cls, type, id, key, fields):
        # Override in subclass if needed
        pass
