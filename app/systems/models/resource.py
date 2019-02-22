from django.db import models

from data.user.models.user import User
from .base import AppModel, DatabaseAccessError
from .facade import ModelFacade

import hashlib


class ResourceModelFacadeMixin(ModelFacade):

    def key(self):
        return 'name'


class ResourceModel(AppModel):

    id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=256)

    created_user = models.ForeignKey(User, null=True, related_name='+', on_delete=models.PROTECT)
    updated_user = models.ForeignKey(User, null=True, related_name='+', on_delete=models.PROTECT)
    
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.id is None:
            self.id = self.get_id()
        
        if self.created is None:
            self.created_user = User.facade.active_user
        else:
            self.updated_user = User.facade.active_user
        
        super().save(*args, **kwargs)


    def get_id():
        type_name = self.__class__.__name__
        values = [type_name]

        for field in list(self.get_id_fields()).sort():
            value = getattr(self, field, None)
            if value is None:
                raise DatabaseAccessError("Field {} does not exist in model {}".format(field, type_name))
            
            values.append(str(value))

        return hashlib.sha256("-".join(values).encode()).hexdigest()
    
    def get_id_fields(self):
        return []
