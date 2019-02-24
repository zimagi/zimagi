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
        return super().to_python(self.decrypt(value))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        return self.encrypt(value)


class EncryptedDataField(EncryptionMixin, models.TextField):

    def to_python(self, value):
        return super().to_python(unserialize(self.decrypt(value)))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        return self.encrypt(serialize(value))


class CSVField(models.TextField):

    def to_python(self, value):
        if not value:
            return []
        return super().to_python(
            [ x.strip() for x in value.split(',') ]
        )

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        if not value:
            return value
        return ",".join([ x.strip() for x in value ])
