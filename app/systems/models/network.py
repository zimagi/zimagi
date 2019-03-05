from django.db import models as django

from data.network.models import Network
from .resource import ResourceModel, ResourceModelFacadeMixin


class NetworkModelFacadeMixin(ResourceModelFacadeMixin):

    def get_field_network_display(self, instance, value, short):
        return str(value)
 
    def get_field_networks_display(self, instance, value, short):
        networks = [ str(x) for x in value.all() ]
        return "\n".join(networks)


class NetworkMixin(django.Model):
    
    network = django.ForeignKey(Network, 
        null = True, 
        on_delete = django.PROTECT, 
        related_name = "%(class)s_relation"
    )
    class Meta:
        abstract = True

class NetworkRelationMixin(django.Model):
 
    networks = django.ManyToManyField(Network, 
        related_name = "%(class)s_relation"
    ) 
    class Meta:
        abstract = True


class NetworkModel(NetworkMixin, ResourceModel):

    class Meta(ResourceModel.Meta):
        abstract = True
        unique_together = ('network', 'name')

    def __str__(self):
        return "{}:{}".format(self.network.name, self.name)

    def get_id_fields(self):
        return ('name', 'network_id')
