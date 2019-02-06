from systems import models
from .firewall import Firewall

import re


class FirewallRuleFacade(models.ProviderModelFacade):

    def __init__(self, cls):
        super().__init__(cls)
        self.fields.append('cidrs')

    def get_packages(self):
        return super().get_packages() + ['network', 'server']

    def key(self):
        return 'name'

    def set_scope(self, firewall):
        super().set_scope(firewall_id = firewall.id)


class FirewallRule(models.AppProviderModel):
    name = models.CharField(max_length=128)
    type = models.CharField(null=True, max_length=128)

    mode = models.CharField(null=True, max_length=10, choices=[(i, i) for i in ('ingress', 'egress')])
    from_port = models.IntegerField(null=True)
    to_port = models.IntegerField(null=True)
    protocol = models.CharField(max_length=10, default='tcp', choices=[(i, i) for i in ('tcp', 'udp', 'icmp')])
    _cidrs = models.TextField(db_column="cidrs", null=True)

    firewall = models.ForeignKey(Firewall, related_name='rules', on_delete=models.PROTECT)
    
    @property
    def cidrs(self):
        if self._cidrs:
            if getattr(self, '_cached_cidrs', None) is None:
                self._cached_cidrs = re.sub(r'\s+', '', self._cidrs).split(',')
            return self._cached_cidrs
        return []

    @cidrs.setter
    def cidrs(self, data):
        if isinstance(data, (list, tuple)):
            data = ",".join([x.strip() for x in data])
        
        self._cidrs = data
        self._cached_cidrs = None


    class Meta:
        unique_together = (
            ('firewall', 'name')
        )
        facade_class = FirewallRuleFacade


    def __str__(self):
        return "{} ({})".format(self.name, self.type)


    def initialize(self, command):
        self.provider = command.get_provider('network:firewall_rule', self.type, instance = self)
        return True
