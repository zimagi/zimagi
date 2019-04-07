from django.db import models

from utility.encryption import Cipher
from utility.data import serialize, unserialize

import re


class EncryptionMixin(object):

    def encrypt(self, value):
        # Python data type
        return Cipher.get('field').encrypt(value).decode()

    def decrypt(self, value):
        # Database cipher text
        return Cipher.get('field').decrypt(str.encode(value))


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
        if value is None:
            return []
        return [ x.strip() for x in value.split(',') ]

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        if value is None:
            return value

        if isinstance(value, (list, tuple)):
            return ",".join([ x.strip() for x in value ])
        return str(value)

    def value_from_object(self, obj):
        value = super().value_from_object(obj)
        return self.get_prep_value(value)

    def value_to_string(self, obj):
        return self.value_from_object(obj)
