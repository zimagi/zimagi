from django.db import models
from django.db.models.base import ModelBase

from .facade import ModelFacade

import inspect


models.options.DEFAULT_NAMES += ('facade_class',)


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
