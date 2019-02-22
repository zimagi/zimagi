from django.db import models
from django.db.models.base import ModelBase
from django.utils.timezone import now

from .facade import ModelFacade

import inspect
import copy


models.options.DEFAULT_NAMES += ('facade_class',)


class DatabaseAccessError(Exception):
    pass


class AppMetaModel(ModelBase):

    def __init__(cls, name, bases, attr):
        if not cls._meta.abstract:
            facade_class = cls._meta.facade_class
            
            if facade_class and inspect.isclass(facade_class):
                cls.facade = facade_class(cls)


class AppModel(models.Model, metaclass = AppMetaModel):

    created = models.DateTimeField(null=True)    
    updated = models.DateTimeField(null=True)
    
    class Meta:
        abstract = True
        facade_class = ModelFacade

    def initialize(self, command):
        return True

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = now()
        else:
            self.updated = now()
        
        with self.facade.thread_lock:
            super().save(*args, **kwargs)

    @property
    def facade(self):
        return copy.deepcopy(self.__class__.facade)
