from data.storage.models import Storage
from data.storage_mount.models import StorageMount
from . import NetworkMixin


class StorageMixin(NetworkMixin):

    schema = {
        'storage': {
            'plural': 'storage',
            'model': Storage,
            'provider': True,                       
            'system_fields': (
                'network',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        },
        'mount': {
            'model': StorageMount,
            'system_fields': (
                'subnet',
                'type',
                'config',
                'variables',
                'state_config',
                'created', 
                'updated'
            )
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade_index['02_storage'] = self._storage
        self.facade_index['03_mount'] = self._mount


    def set_storage_scope(self):
        if self.storage_name and ':' in self.storage_name:
            components = self.storage_name.split(':')
            self.options.add('network_name', components[0].strip())
            self.options.add('storage_name', components[1].strip())

        if self.network_name:
            self._storage.set_scope(self.network)


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
