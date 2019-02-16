from django.db import models
from django.db.models.base import ModelBase
from django.utils.timezone import now

from .facade import ModelFacade

import inspect
import json
import copy


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

    def save(self, *args, **kwargs):
        if not getattr(self, 'created', None):
            self.created = now()
        else:
            self.updated = now()
        
        super().save(*args, **kwargs)


    @property
    def facade(self):
        return copy.deepcopy(self.__class__.facade)


class ConfigModelFacade(ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)
        self.fields.append('config')


class AppConfigModel(AppModel):

    _config = models.TextField(db_column="config", default='{}')
    
    @property
    def config(self):
        if getattr(self, '_cached_config', None) is None:        
            self._cached_config = json.loads(self._config)
        return self._cached_config

    @config.setter
    def config(self, data):
        if not isinstance(data, str):
            data = json.dumps(data)
        
        self._config = data
        self._cached_config = None


    class Meta:
        abstract = True
        facade_class = ConfigModelFacade
    

    def save(self, *args, **kwargs):
        self.config = self.config
        return super().save(*args, **kwargs)



class ProviderModelFacade(ConfigModelFacade):

    def __init__(self, cls):
        super().__init__(cls)
        self.fields.extend(['variables', 'state'])


class AppProviderModel(AppConfigModel):

    _variables = models.TextField(db_column="variables", default='{}')
    _state_config = models.TextField(db_column="state", default='{}')


    @property
    def variables(self):
        if getattr(self, '_cached_variables', None) is None:        
            self._cached_variables = json.loads(self._variables)
        return self._cached_variables

    @variables.setter
    def variables(self, data):
        if not isinstance(data, str):
            data = json.dumps(data)
        
        self._variables = data
        self._cached_variables = None

    
    @property
    def state(self):
        if getattr(self, '_cached_state', None) is None:        
            self._cached_state = json.loads(self._state_config)
        return self._cached_state

    @state.setter
    def state(self, data):
        if not isinstance(data, str):
            data = json.dumps(data)
        
        self._state_config = data
        self._cached_state = None


    class Meta:
        abstract = True
        facade_class = ProviderModelFacade


    def save(self, *args, **kwargs):
        self.variables = self.variables
        self.state = self.state
        return super().save(*args, **kwargs)
