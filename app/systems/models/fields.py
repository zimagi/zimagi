from django.db import models

from utility.encryption import Cipher
from utility.data import serialize, unserialize

import re


class EncryptionMixin(object):

    def to_python(self, value):
        if value is None:
            return value
        #value = Cipher.get('field').decrypt(value)
        #return super().to_python(unserialize(value))
        return super().to_python(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_db_prep_save(self, value, connection):
        value = super().get_db_prep_save(value, connection)
        if value is None:
            return value
        #return Cipher.get('field').encrypt(serialize(value))
        #return serialize(value)
        return str(value)


class EncryptedCharField(EncryptionMixin, models.CharField):
    pass

class EncryptedTextField(EncryptionMixin, models.TextField):
    pass


class CSVField(models.TextField):

    def to_python(self, value):
        if value is None:
            return value
        return super().to_python(
            [ x.strip() for x in value.split(',') ]
        )

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_db_prep_save(self, value, connection):
        value = super().get_db_prep_save(value, connection)
        if value is None:
            return value
        return ",".join([ x.strip() for x in value ])
