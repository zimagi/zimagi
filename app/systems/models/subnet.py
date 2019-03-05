from django.db import models as django

from data.subnet.models import Subnet
from .resource import ResourceModel, ResourceModelFacadeMixin


class SubnetModelFacadeMixin(ResourceModelFacadeMixin):

    def get_field_subnet_display(self, instance, value, short):
        return str(value)
 
    def get_field_subnets_display(self, instance, value, short):
        subnets = [ str(x) for x in value.all() ]
        return "\n".join(subnets)


class SubnetMixin(django.Model):
    
    subnet = django.ForeignKey(Subnet, 
        null = True, 
        on_delete = django.PROTECT, 
        related_name = "%(class)s_relation"
    )
    class Meta:
        abstract = True

class SubnetRelationMixin(django.Model):
 
    subnets = django.ManyToManyField(Subnet, 
        related_name = "%(class)s_relation"
    ) 
    class Meta:
        abstract = True


class SubnetModel(SubnetMixin, ResourceModel):

    class Meta(ResourceModel.Meta):
        abstract = True
        unique_together = ('subnet', 'name')

    def __str__(self):
        return "{}:{}".format(self.subnet.name, self.name)

    def get_id_fields(self):
        return ('name', 'subnet_id')
