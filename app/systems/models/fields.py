from django.db import models
from utility.data import serialize, unserialize


class DataField(models.TextField):
    def to_python(self, value):
        return unserialize(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        return serialize(value)

    def value_from_object(self, obj):
        value = super().value_from_object(obj)
        return self.get_prep_value(value)

    def value_to_string(self, obj):
        return self.value_from_object(obj)


class ListField(models.JSONField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = list
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class DictionaryField(models.JSONField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = dict
        kwargs["null"] = False
        super().__init__(*args, **kwargs)
