from django.db import models as django

from data.environment.models import Environment
from .resource import ResourceModel, ResourceModelFacadeMixin


class EnvironmentModelFacadeMixin(ResourceModelFacadeMixin):

    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }


class EnvironmentMixin(django.Model):

    environment = django.ForeignKey(Environment, null=True, on_delete=django.PROTECT)

    class Meta:
        abstract = True


class EnvironmentModel(EnvironmentMixin, ResourceModel):

    class Meta(ResourceModel.Meta):
        abstract = True
        unique_together = ('environment', 'name')

    def __str__(self):
        return "{}:{}".format(self.environment.name, self.name)
   
    def get_id_fields(self):
        return ('name', 'environment_id')
