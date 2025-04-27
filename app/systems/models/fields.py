from django.db import models

from utility.data import dump_json, load_json, serialize, unserialize


class FieldError(Exception):
    pass


class EncryptionMixin:
    def encrypt(self, value):
        from systems.encryption.cipher import Cipher

        # Python data type
        return Cipher.get("data").encrypt(value).decode()

    def decrypt(self, value):
        from systems.encryption.cipher import Cipher

        # Database cipher text
        return Cipher.get("data").decrypt(str.encode(value))


class EncryptedCharField(EncryptionMixin, models.CharField):
    def to_python(self, value):
        if not value:
            return value
        return self.decrypt(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        if not value:
            return value
        return self.encrypt(value)

    def value_from_object(self, obj):
        value = super().value_from_object(obj)
        return self.get_prep_value(value)

    def value_to_string(self, obj):
        return self.value_from_object(obj)


class EncryptedDataField(EncryptionMixin, models.TextField):
    def to_python(self, value):
        return unserialize(self.decrypt(value))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        return self.encrypt(serialize(value))

    def value_from_object(self, obj):
        value = super().value_from_object(obj)
        return self.get_prep_value(value)

    def value_to_string(self, obj):
        return self.value_from_object(obj)


class CSVField(models.TextField):
    def to_python(self, value):
        if value is None or value == "":
            return []
        return [x.strip() for x in value.split(",")]

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        if isinstance(value, (list, tuple)):
            return ",".join([str(x).strip() for x in value])
        return str(value)

    def value_from_object(self, obj):
        value = super().value_from_object(obj)
        return self.get_prep_value(value)

    def value_to_string(self, obj):
        return self.value_from_object(obj)


class BaseJSONField(models.JSONField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return load_json(value, cls=self.decoder)

    def get_prep_value(self, value):
        if value is None:
            return value
        return dump_json(value, cls=self.encoder)


class ListField(BaseJSONField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = list
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class DictionaryField(BaseJSONField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = dict
        kwargs["null"] = False
        super().__init__(*args, **kwargs)
