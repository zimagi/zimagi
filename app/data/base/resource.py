from django.utils.timezone import now

from systems.models.base import DatabaseAccessError
from systems.models.index import BaseModel, BaseModelFacade

import hashlib


class ResourceBase(BaseModel('resource')):

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = now()

        filters = {}
        self.facade._check_scope(filters)
        for field, value in filters.items():
            if value is not None:
                setattr(self, field, value)

        if not self.id:
            self.id = self.get_id()

        super().save(*args, **kwargs)


    def get_id_values(self):
        values = []
        fields = list(self.get_id_fields())
        fields.sort()

        if not fields:
            fields = [ 'name' ]

        for field in fields:
            value = getattr(self, field, None)
            if value is None:
                raise DatabaseAccessError("Field {} does not exist in model {}".format(field, str(self)))
            values.append(str(value))

        return values

    def get_id(self):
        hasher = hashlib.blake2b(digest_size = 8)
        hasher.update("-".join(self.get_id_values()).encode())
        return "{}{}".format(
            self.created.strftime("%Y%m%d%H%M%S%f"),
            hasher.hexdigest()
        )
