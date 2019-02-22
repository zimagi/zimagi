from systems import models

from data.environment import models as env
from .resource import ResourceModel, ResourceModelFacadeMixin


class EnvironmentModelFacadeMixin(ResourceModelFacadeMixin):

    def scope(self, fields = False):
        if fields:
            return ('environment',)
        
        curr_env = env.Environment.facade.get_env()
        if not curr_env:
            return False

        return { 'environment_id': curr_env }


class EnvironmentMixin(object):

    environment = models.ForeignKey(env.Environment, on_delete=models.PROTECT)


class EnvironmentModel(EnvironmentMixin, ResourceModel):

    class Meta:
        abstract = True
        unique_together = ('environment', 'name')

    def __str__(self):
        return "{}:{}".format(self.environment.name, self.name)
   
    def get_id_fields(self):
        return ('name', 'environment_id')
