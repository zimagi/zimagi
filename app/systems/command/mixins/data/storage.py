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
                'environment',
                'storage',
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
