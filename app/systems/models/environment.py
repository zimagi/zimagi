from django.db import models as django

from data.environment.models import Environment
from .resource import ResourceModel, ResourceModelFacadeMixin


class EnvironmentModelFacadeMixin(ResourceModelFacadeMixin):

    def scope(self, fields = False):
        if fields:
            return ('environment',)

        curr_env = Environment.facade.get_env_id()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }

    def get_field_environment_display(self, instance, value, short):
        return str(value)


class EnvironmentMixin(django.Model):

    environment = django.ForeignKey(Environment,
        null = True,
        on_delete = django.PROTECT,
        related_name = "%(class)s_relation"
    )
    class Meta:
        abstract = True


class EnvironmentModel(EnvironmentMixin, ResourceModel):

    class Meta(ResourceModel.Meta):
        abstract = True
        unique_together = ('environment', 'name')

    def __str__(self):
        return "{}".format(self.name)

    def get_id_fields(self):
        return ('name', 'environment_id')
