from django.db import models as django

from data.environment.models import Environment
from .resource import ResourceModel, ResourceModelFacadeMixin


class EnvironmentModelFacadeMixin(ResourceModelFacadeMixin):

    def get_base_scope(self):
        return { 'environment_id': Environment.facade.get_env() }

    def get_field_environment_display(self, instance, value, short):
        return self.relation_color(str(value))


class EnvironmentMixin(django.Model):

    environment = django.ForeignKey(Environment,
        null = True,
        on_delete = django.PROTECT,
        related_name = "%(class)s_relation",
        editable = False
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
