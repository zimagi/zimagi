from django.db import models
from django.db.models.base import ModelBase

from .facade import ModelFacade

import inspect


class AppMetaModel(ModelBase):

    def __new__(cls, name, bases, attr):
        meta_class = attr.get('Meta', None)

        if meta_class and inspect.isclass(meta_class):
            facade_class = getattr(meta_class, 'facade_class', None)
        
            if facade_class and inspect.isclass(facade_class):
                attr['facade'] = facade_class(cls, meta_class)
            
        if 'facade' not in attr:
            attr['facade'] = ModelFacade(cls, meta_class)
        
        return super().__new__(cls, name, bases, attr)


class AppModel(models.Model, metaclass = AppMetaModel):

    created = models.DateTimeField(null=True)
    updated = models.DateTimeField(null=True)
    
    class Meta:
        facade_class = ModelFacade
