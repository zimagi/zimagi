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

    def set_network_scope(self, network):
        super().set_scope(subnet__network__id = network.id)

    def set_subnet_scope(self, subnet):
        super().set_scope(subnet_id = subnet.id)


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

    def initialize(self, command):
        if not super().initialize(command):
            return False
        
        self.status = self.STATUS_RUNNING if self.ping() else self.STATUS_UNREACHABLE
        return True


    def running(self):
        if self.status == self.STATUS_RUNNING:
            return True
        return False

    def ping(self, port = 22):
        return self.provider.ping(port = port)
