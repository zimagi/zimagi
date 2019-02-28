from django.db import models as django

from .base import AppModel, DatabaseAccessError
from .facade import ModelFacade

import hashlib


class ResourceModelFacadeMixin(ModelFacade):

    def key(self):
        return 'name'
 
    def default_order(self):
        return 'name'
   
    def get_field_id_display(self, instance, value, short):
        return value
    
    def get_field_name_display(self, instance, value, short):
        return value


class ResourceModel(AppModel):

    id = django.CharField(primary_key=True, max_length=64)
    name = django.CharField(max_length=256)
    
    class Meta(AppModel.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.get_id()
        
        super().save(*args, **kwargs)


    def get_id(self):
        type_name = self.__class__.__name__
        values = [type_name]

        fields = list(self.get_id_fields())
        fields.sort()

        for field in fields:
            value = getattr(self, field, None)
            if value is None:
                raise DatabaseAccessError("Field {} does not exist in model {}".format(field, type_name))
            
            values.append(str(value))

        return hashlib.sha256("-".join(values).encode()).hexdigest()
    
    def get_id_fields(self):
        return []
