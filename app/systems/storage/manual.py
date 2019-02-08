from .base import *


class ManualStorageMountProvider(StorageMountProvider):

    def provider_config(self, type = None):
        super().provider_config(type)
        self.requirement(str, 'remote_host', help = 'Remote host to connect storage mount')
        self.option(str, 'remote_path', '/', help = 'Remote path to mount locally', config_name = 'manual_remote_path')


class Manual(BaseStorageProvider):
    
    def register_types(self):
        super().register_types()
        self.set('mount', ManualStorageMountProvider)
