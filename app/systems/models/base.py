from django.db import models as django
from django.db.models.base import ModelBase
from django.db.models.manager import Manager
from django.utils.timezone import now

from .facade import ModelFacade

import inspect
import copy


django.options.DEFAULT_NAMES += (
    'facade_class',
    'scope',
    'provider_name',
    'provider_relation'
)


class DatabaseAccessError(Exception):
    pass


class AppMetaModel(ModelBase):

    def __init__(cls, name, bases, attr):
        if not cls._meta.abstract:
            facade_class = cls._meta.facade_class

            if facade_class and inspect.isclass(facade_class):
                cls.facade = facade_class(cls)


class BaseModelMixin(django.Model):

    created = django.DateTimeField(null = True, editable = False)
    updated = django.DateTimeField(null = True, editable = False)

    class Meta:
        abstract = True

    def initialize(self, command):
        return True

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = now()
        else:
            self.updated = now()

        with self.facade.thread_lock:
            super().save(*args, **kwargs)

    def save_related(self, provider):
        relations = self.facade.get_relations()
        for field, value in provider.command.get_relations(self.facade).items():
            if value is not None:
                facade = provider.command.facade(relations[field]['name'])
                if relations[field]['multiple']:
                    provider.update_related(self, field, facade, value)
                else:
                    value = None if not value else value
                    provider.set_related(self, field, facade, value)

    @property
    def facade(self):
        return copy.deepcopy(self.__class__.facade)


class AppModel(
    BaseModelMixin,
    metaclass = AppMetaModel
):
    class Meta:
        abstract = True
        facade_class = ModelFacade
        ordering = ['-created']
