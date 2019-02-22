from systems import models
from systems.models import firewall, provider


class FirewallRuleFacade(
    provider.ProviderModelFacadeMixin,
    firewall.FirewallModelFacadeMixin
):
    pass


class FirewallRule(
    provider.ProviderMixin,
    firewall.FirewallModel
):
    mode = models.CharField(null=True, max_length=10, choices=[(i, i) for i in ('ingress', 'egress')])
    from_port = models.IntegerField(null=True)
    to_port = models.IntegerField(null=True)
    protocol = models.CharField(max_length=10, default='tcp', choices=[(i, i) for i in ('tcp', 'udp', 'icmp')])
    cidrs = models.CSVField(null=True)

    class Meta:
        facade_class = FirewallRuleFacade

    def __str__(self):
        return "{}".format(self.name)

    def get_provider_name(self):
        return 'network:firewall_rule'
