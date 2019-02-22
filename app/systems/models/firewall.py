from systems import models

from data.network import models as network
from .resource import ResourceModel, ResourceModelFacadeMixin


class FirewallModelFacadeMixin(ResourceModelFacadeMixin):

    def set_scope(self, firewall):
        super().set_scope(firewall_id = firewall.id)


class FirewallMixin(object):
    
    firewall = models.ForeignKey(network.Firewall, on_delete=models.PROTECT)


class FirewallModel(FirewallMixin, ResourceModel):

    class Meta:
        abstract = True
        unique_together = ('firewall', 'name')

    def __str__(self):
        return "{}:{}".format(self.firewall.name, self.name)

    def get_id_fields(self):
        return ('name', 'firewall_id')
