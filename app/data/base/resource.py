from systems.models.base import DatabaseAccessError
from systems.models.index import BaseModel, BaseModelFacade

import hashlib


class ResourceBase(BaseModel('resource')):

    def save(self, *args, **kwargs):
        filters = {}
        self.facade._check_scope(filters)
        for field, value in filters.items():
            if value is not None:
                setattr(self, field, value)

        if not self.id:
            self.id = self.get_id()

        super().save(*args, **kwargs)


    def get_id_values(self):
        type_name = self.__class__.__name__
        values = [type_name]

        fields = list(self.get_id_fields())
        fields.sort()

        for field in fields:
            value = getattr(self, field, None)
            if value is None:
                raise DatabaseAccessError("Field {} does not exist in model {}".format(field, type_name))

            values.append(str(value))

        return values

    def get_id(self):
        values = self.get_id_values()
        return hashlib.sha256("-".join(values).encode()).hexdigest()
