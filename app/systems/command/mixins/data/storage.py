from django.core.management.base import CommandError

from . import DataMixin
from data.storage import models

import re
import json


class StorageMixin(DataMixin):

    def parse_storage_provider_name(self, optional = False, help_text = 'storage resource provider'):
        self.parse_variable('storage_provider_name', optional, str, help_text)

    @property
    def storage_provider_name(self):
        return self.options.get('storage_provider_name', None)

    @property
    def storage_provider(self):
        return self.get_provider('storage', self.storage_provider_name)


    def parse_storage_name(self, optional = False, help_text = 'unique environment storage name'):
        self.parse_variable('storage_name', optional, str, help_text)

    @property
    def storage_name(self):
        return self.options.get('storage_name', None)

    @property
    def mount(self):
        return self.get_instance(self._storage, self.storage_name)


    def parse_storage_reference(self, optional = False, help_text = 'unique environment storage name'):
        self.parse_variable('storage_reference', optional, str, help_text)

    @property
    def storage_reference(self):
        return self.options.get('storage_reference', None)

    @property
    def mounts(self):
        return self.get_instances_by_reference(self._storage, self.storage_reference)


    def parse_storage_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._storage, 'storage_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                'config'
            ),
            help_callback
        )

    @property
    def storage_fields(self):
        return self.options.get('storage_fields', {})


    @property
    def _storage(self):
        return models.Storage.facade


    def initialize_instance(self, facade, storage):
        storage.provider = self.get_provider('storage', storage.type, storage = storage)
        storage.state = None
