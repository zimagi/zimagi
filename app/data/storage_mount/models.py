from django.db import models as django

from systems.models import environment, subnet, storage, firewall, provider


class StorageMountFacade(
    provider.ProviderModelFacadeMixin,
    subnet.SubnetModelFacadeMixin,
    storage.StorageModelFacadeMixin,
    firewall.FirewallModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def get_provider_name(self):
        return 'storage:mount'
    
    def get_provider_relation(self):
        return 'storage'
    
    def get_scopes(self):
        return (
            'network',
            'subnet',
            'storage'
        )
    
    def get_relations(self):
        return {
            'firewalls': ('firewall', 'Firewalls', '--firewalls')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('subnet', 'Subnet'),
            ('storage', 'Storage'),
            ('type', 'Type'),            
            ('remote_host', 'Remote host'),
            ('remote_path', 'Remote path'),
        )
    
    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('subnet', 'Subnet'),
            ('storage', 'Storage'),
            ('type', 'Type'),
            '---',
            ('remote_host', 'Remote host'),
            ('remote_path', 'Remote path'),
            ('mount_options', 'Mount options'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('variables', 'Variables'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )
    
    def get_field_remote_host_display(self, instance, value, short):
        return value
    
    def get_field_remote_path_display(self, instance, value, short):
        return value
    
    def get_field_mount_options_display(self, instance, value, short):
        return value


class StorageMount(
    provider.ProviderMixin,
    subnet.SubnetMixin,
    storage.StorageMixin,
    firewall.FirewallRelationMixin,
    environment.EnvironmentModel  
):    
    remote_host = django.CharField(null=True, max_length=128)
    remote_path = django.CharField(null=True, max_length=256)
    mount_options = django.TextField(null=True)
    
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = StorageMountFacade

    def __str__(self):
        return "{} ({}:{})".format(self.name, self.remote_host, self.remote_path)
