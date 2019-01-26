from django.db import models
from django.db.models.base import ModelBase

from .facade import ModelFacade

import inspect
import json


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


    def initialize(self, command):
        return True


class ConfigModelFacade(ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)
        self.fields.append('config')


class AppConfigModel(AppModel):

    _config = models.TextField(db_column="config", null=True)
    
    @property
    def config(self):
        if self._config:
            if getattr(self, '_cached_config', None) is None:        
                self._cached_config = json.loads(self._config)
            return self._cached_config
        return {}

    @config.setter
    def config(self, data):
        if not isinstance(data, str):
            data = json.dumps(data)
        
        self._config = data
        self._cached_config = None


    class Meta:
        abstract = True
        facade_class = ConfigModelFacade
