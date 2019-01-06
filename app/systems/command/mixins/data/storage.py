from django.core.management.base import CommandError

from .base import DataMixin
from data.project import models

import re
import json


class StorageMixin(DataMixin):

    def parse_storage_provider_name(self, optional = False, help_text = 'storage resource provider'):
        self._parse_variable('storage_provider_name', str, help_text, optional)

    @property
    def storage_provider_name(self):
        return self.options.get('storage_provider_name', None)

    @property
    def storage_provider(self):
        if not getattr(self, '_storage_provider', None):
            self._storage_provider = self.get_storage(self.storage_provider_name)
        return self._storage_provider


    def parse_storage_name(self, optional = False, help_text = 'unique environment storage name'):
        self._parse_variable('storage_name', str, help_text, optional)

    @property
    def storage_name(self):
        return self.options.get('storage_name', None)

    @property
    def mount(self):
        self._data_mount = self._load_instance(
            self._storage, self.storage_name, 
            getattr(self, '_data_mount', None)
        )
        return self._data_mount


    def parse_storage_reference(self, optional = False, help_text = 'unique environment storage name'):
        self._parse_variable('storage_reference', str, help_text, optional)

    @property
    def storage_reference(self):
        return self.options.get('storage_reference', None)

    @property
    def mounts(self):
        if not getattr(self, '_data_mounts', None):
            self._data_mounts = self.get_storage_by_reference(self.storage_reference)
        return self._data_mounts


    def parse_storage_fields(self, optional = False, help_callback = None):
        self._parse_fields(self._storage, 'storage_fields', optional, 
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


    def get_storage_by_reference(self, reference = None, error_on_empty = True):
        storage_results = []
        if reference and reference != 'all':
            matches = re.search(r'^([^\=]+)\s*\=\s*(.+)', reference)

            if matches:
                field = matches.group(1)
                value = matches.group(2)

                if field != 'state':
                    storage_mounts = self._storage.query(**{ field: value })
                else:
                    storage_mounts = self._storage.all()
                    states = [value]
                    
                if len(storage_mounts) > 0:
                    storage_results.extend(self.get_storage(
                        instances = list(storage_mounts), 
                        states = states
                    ))
            else:
                storage = self._storage.retrieve(reference)
                if storage:
                    storage_results.extend(self.get_storage(instances = storage))
        else:
            storage_results.extend(self.get_storage())
        
        if error_on_empty and not storage_results:
            if reference:
                self.warning("No storage mounts were found: {}".format(reference))
            else:
                self.warning("No storage mounts were found")
        
        return storage_results

    def get_storage(self, names = [], instances = [], states = None):
        storage_items = []
        storage_mounts = []

        if not getattr(self, '_data_storage_cache', None):
            self._data_storage_cache = {}

        if isinstance(names, str):
            names = [names]
        
        if names:
            storage_items.extend(names)

        if not isinstance(instances, (list, tuple)):
            instances = [instances]

        if instances:
            storage_items.extend(instances)

        if states and not isinstance(states, (list, tuple)):
            states = [states]

        if not storage_items and not names and not instances and not states:
            storage_items = self._storage.all()            

        def init_storage(storage, state):
            if isinstance(storage, str):
                storage = self._storage.retrieve(storage)
            if storage:
                if not storage.name in self._data_storage_cache:
                    if isinstance(storage.config, str):
                        storage.config = json.loads(storage.config)
                    
                    storage.storage_provider = self.get_storage_provider(storage.type, storage = storage)
                    storage.state = None
                    self._data_storage_cache[storage.name] = storage
                else:
                    storage = self._data_storage_cache[storage.name]

                if not states or storage.state in states:
                    storage_mounts.append(storage)
            else:
                self.error("Storage mount {} does not exist".format(name))

        self.run_list(storage_items, init_storage)
        return storage_mounts
