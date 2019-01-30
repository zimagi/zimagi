from django.core.management.base import CommandError

from . import NetworkMixin
from data.storage import models

import re
import json


class StorageMixin(NetworkMixin):

    def parse_storage_provider_name(self, optional = False, help_text = 'storage resource provider'):
        self.parse_variable('storage_provider_name', optional, str, help_text, 'NAME')

    @property
    def storage_provider_name(self):
        return self.options.get('storage_provider_name', None)

    @property
    def storage_provider(self):
        return self.get_provider('storage', self.storage_provider_name)


    def parse_storage_name(self, optional = False, help_text = 'unique environment storage name (defaults to @storage)'):
        self.parse_variable('storage_name', optional, str, help_text, 'NAME')

    @property
    def storage_name(self):
        name = self.options.get('storage_name', None)
        if not name:
            name = self.get_config('storage', required = False)
        return name

    def set_storage_scope(self):
        if self.storage_name and ':' in self.storage_name:
            components = self.storage_name.split(':')
            self.options.add('network_name', components[0].strip())
            self.options.add('storage_name', components[1].strip())

        if self.network_name:
            self._storage.set_scope(self.network)

    @property
    def storage_source(self):
        return self.get_instance(self._storage, self.storage_name)

    @property
    def storage_sources(self):
        return self.get_instances(self._storage)

    def parse_storage_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._storage, 'storage_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                '_config'
            ),
            help_callback,
            callback_args = ['storage']
        )

    @property
    def storage_fields(self):
        return self.options.get('storage_fields', {})

    
    def parse_mount_name(self, optional = False, help_text = 'unique environment storage mount name'):
        self.parse_variable('mount_name', optional, str, help_text, 'NAME')

    @property
    def mount_name(self):
        return self.options.get('mount_name', None)

    def set_mount_scope(self):
        if self.mount_name and ':' in self.mount_name:
            components = self.mount_name.split(':')
            component_count = len(components)

            if component_count == 3:
                self.options.add('network_name', components[0].strip())
                self.options.add('storage_name', components[1].strip())
                self.options.add('mount_name', components[2].strip())
            elif component_count == 2:
                self.options.add('storage_name', components[0].strip())
                self.options.add('mount_name', components[1].strip())
            else:
                self.error("Wrong number of mount sections; need 'network:storage:mount' or 'storage:mount' with '@network' defined".format())

        self._storage.set_scope(self.network)
        self._mount.set_scope(self.storage_source)

    @property
    def mount(self):
        return self.get_instance(self._mount, self.mount_name)

    @property
    def mounts(self):
        return self.get_instances(self._mount)

    def parse_mount_fields(self, optional = False, help_callback = None):
        self.parse_fields(self._storage, 'mount_fields', optional, 
            (
                'created', 
                'updated', 
                'environment',
                '_config'
            ),
            help_callback,
            callback_args = ['mount']
        )

    @property
    def mount_fields(self):
        return self.options.get('mount_fields', {})


    @property
    def _storage(self):
        return self.facade(models.Storage.facade)

    @property
    def _mount(self):
        return self.facade(models.StorageMount.facade)
