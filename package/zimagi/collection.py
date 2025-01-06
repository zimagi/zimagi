import copy

from . import utility


class Collection:
    def __init__(self, attributes):
        attributes = utility.normalize_value(copy.deepcopy(attributes), strip_quotes=False, parse_json=True)
        for key, value in attributes.items():
            setattr(self, key, value)

    def keys(self):
        return self.__dict__.keys()

    def __setitem__(self, name, value):
        self.__dict__[name] = value

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def set(self, name, value):
        self.__setitem__(name, value)

    def __getitem__(self, name):
        if name not in self.__dict__:
            return None
        return self.__dict__[name]

    def __getattr__(self, name):
        return self.__getitem__(name)

    def get(self, name, default=None):
        if name not in self.__dict__:
            return default
        return self.__dict__[name]

    def export(self):
        for key, value in self.__dict__.items():
            if isinstance(value, Collection):
                self.__dict__[key] = value.export()
            elif isinstance(value, dict):
                for dict_key, dict_value in value.items():
                    if isinstance(dict_value, Collection):
                        self.__dict__[key][dict_key] = dict_value.export()
            elif isinstance(value, (list, tuple)):
                for index, list_value in enumerate(value):
                    if isinstance(list_value, Collection):
                        self.__dict__[key][index] = list_value.export()

        return copy.deepcopy(self.__dict__)

    def __str__(self):
        def convert(data):
            if isinstance(data, Collection):
                data = data.__dict__

            if isinstance(data, dict):
                for key, value in data.items():
                    data[key] = convert(value)
            elif isinstance(data, (list, tuple)):
                for index, value in enumerate(data):
                    data[index] = convert(value)
            return data

        return utility.dump_json(convert(self), indent=2)

    def __repr__(self):
        return self.__str__()

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for key, value in self.__dict__.items():
            setattr(result, key, copy.deepcopy(value, memo))
        return result


class RecursiveCollection(Collection):
    def __init__(self, attributes):
        for property, value in attributes.items():
            attributes[property] = self._create_collections(value)

        super().__init__(attributes)

    def _create_collections(self, data):
        conversion = data

        if isinstance(data, (list, tuple)):
            conversion = []
            for value in data:
                conversion.append(self._create_collections(value))

        elif isinstance(data, dict):
            conversion = RecursiveCollection(data)

        return conversion
