from django.db import models as django

from data.firewall.models import Firewall
from .resource import ResourceModel, ResourceModelFacadeMixin


class FirewallModelFacadeMixin(ResourceModelFacadeMixin):

    def set_scope(self, firewall):
        super().set_scope(firewall_id = firewall.id)

    def get_field_firewall_display(self, firewall):
        return ('Firewall', str(firewall))
 
    def get_field_firewalls_display(self, manager):
        firewalls = [ str(x) for x in manager.all() ]
        return ('Firewalls', "\n".join(firewalls))


class FirewallMixin(django.Model):
    
    firewall = django.ForeignKey(Firewall, null=True, on_delete=django.PROTECT, related_name='+')

    class Meta:
        abstract = True

class FirewallRelationMixin(django.Model):
 
    firewalls = django.ManyToManyField(Firewall, related_name='+')
 
    class Meta:
        abstract = True


class FirewallModel(FirewallMixin, ResourceModel):

    class Meta(ResourceModel.Meta):
        abstract = True
        unique_together = ('firewall', 'name')

    def __str__(self):
        return "{}:{}".format(self.firewall.name, self.name)

    def get_id_fields(self):
        return ('name', 'firewall_id')
