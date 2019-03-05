from .base import *


class InternalStorageMountProvider(StorageMountProvider):

    def provider_config(self, type = None):
        super().provider_config(type)
        self.requirement(str, 'remote_host', help = 'Remote host to connect storage mount')
        self.option(str, 'remote_path', '/', help = 'Remote path to mount locally', config_name = 'internal_remote_path')


class Internal(BaseStorageProvider):
    
    def register_types(self):
        super().register_types()
        self.set('mount', InternalStorageMountProvider)
