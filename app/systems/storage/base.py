from django.conf import settings

from systems.command import providers


class StorageProvider(providers.TerraformProvider):
    
    def terraform_type(self):
        return 'storage'

    @property
    def facade(self):
        return self.command._storage

    def create(self, name, network, fields):
        fields['type'] = self.name
        fields['network'] = network
        return super().create(name, fields)


class StorageMountProvider(providers.TerraformProvider):

    def provider_config(self, type = None):
        self.option(str, 'mount_options', 'nfs4 rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0', help = 'Mount options', config_name = 'manual_mount_options')

    def terraform_type(self):
        return 'storage_mount'

    @property
    def facade(self):
        return self.command._mount

    def create(self, storage, subnet, fields, **relations):
        fields['type'] = self.name
        fields['storage'] = storage
        fields['subnet'] = subnet
        return super().create(subnet.name, fields, **relations)

    def initialize_terraform(self, instance, relations, created):
        if 'firewalls' not in relations:
            relations['firewalls'] = []

        if 'nfs' not in relations['firewalls']:
            firewall = self.command._firewall.retrieve('nfs')
            if firewall:
                relations['firewalls'].append('nfs')


class BaseStorageProvider(providers.MetaCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'storage'
        self.provider_options = settings.STORAGE_PROVIDERS
    
    def register_types(self):
        self.set('storage', StorageProvider)
        self.set('mount', StorageMountProvider)
