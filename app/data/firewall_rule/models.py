from django.db import models as django

from systems.models import fields, firewall, provider


class FirewallRuleFacade(
    provider.ProviderModelFacadeMixin,
    firewall.FirewallModelFacadeMixin
):
    pass


class FirewallRule(
    provider.ProviderMixin,
    firewall.FirewallModel
):
    mode = django.CharField(max_length=10, default='ingress', choices=[(i, i) for i in ('ingress', 'egress')])
    from_port = django.IntegerField(null=True)
    to_port = django.IntegerField(null=True)
    protocol = django.CharField(max_length=10, default='tcp', choices=[(i, i) for i in ('tcp', 'udp', 'icmp')])
    cidrs = fields.CSVField(null=True)

    class Meta(firewall.FirewallModel.Meta):
        facade_class = FirewallRuleFacade

    def __str__(self):
        return "{}".format(self.name)

    def get_provider_name(self):
        return 'network:firewall_rule'
