from django.db import models as django

from settings import Roles
from systems.models import fields, environment, subnet, firewall, provider, group


class ServerFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def get_provider_name(self):
        return 'compute'
    
    def get_scopes(self):
        return (
            'network',
            'subnet'
        )
        
    def get_relations(self):
        return {
            'groups': ('group', 'Groups', '--groups'),
            'firewalls': ('firewall', 'Firewalls', '--firewalls')
        }

    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('subnet', 'Subnet'),
            ('type', 'Type'),
            ('status', 'Status'),
            ('public_ip', 'Public IP'),
            ('private_ip', 'Private IP'),
            ('user', 'User'),
            ('password', 'Password'),
            ('private_key', 'Private key')
        )
    
    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('subnet', 'Subnet'),
            ('type', 'Type'),
            ('status', 'Status'),
            '---',
            ('public_ip', 'Public IP'),
            ('private_ip', 'Private IP'),
            ('user', 'User'),
            ('password', 'Password'),
            ('private_key', 'Private key'),
            ('data_device', 'Data device'),
            ('backup_device', 'Backup device'),
            '---',
            ('config', 'Configuration'),
            '---',
            ('variables', 'Variables'),
            ('state_config', 'State'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )
    
    def get_field_public_ip_display(self, instance, value, short):
        return value
    
    def get_field_private_ip_display(self, instance, value, short):
        return value
    
    def get_field_user_display(self, instance, value, short):
        return value
    
    def get_field_password_display(self, instance, value, short):
        if short:
            return '*****' if value else None
        return value
    
    def get_field_private_key_display(self, instance, value, short):
        if short:
            return '*****' if value else None
        return value
    
    def get_field_data_device_display(self, instance, value, short):
        return value
    
    def get_field_backup_device_display(self, instance, value, short):
        return value

    def get_field_status_display(self, instance, value, short):
        return self.model.STATUS_RUNNING if self.ping() else self.model.STATUS_UNREACHABLE

    def ping(self, port = 22):
        return self.model.provider.ping(port = port)


class Server(
    provider.ProviderMixin,
    group.GroupMixin,
    subnet.SubnetMixin,
    firewall.FirewallRelationMixin,
    environment.EnvironmentModel
):
    public_ip = django.CharField(null=True, max_length=128)
    private_ip = django.CharField(null=True, max_length=128)
    user = django.CharField(null=True, max_length=128)
    password = fields.EncryptedCharField(null=True, max_length=1096)
    private_key = fields.EncryptedDataField(null=True)
    data_device = django.CharField(null=True, max_length=256)
    backup_device = django.CharField(null=True, max_length=256)
   
    class Meta(environment.EnvironmentModel.Meta):
        facade_class = ServerFacade

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STATUS_RUNNING = 'running'
        self.STATUS_UNREACHABLE = 'unreachable'

    def __str__(self):
        return "{} ({})".format(self.name, self.ip)

    @property
    def ip(self):
        return self.public_ip if self.public_ip else self.private_ip


    def allowed_groups(self):
        return [ Roles.admin, Roles.server_admin ]

    def running(self):
        if self.status == self.STATUS_RUNNING:
            return True
        return False
