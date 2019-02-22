from django.conf import settings

from systems import models
from systems.models import environment, provider


class ProjectFacade(
    provider.ProviderModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def ensure(self, env, user):
        if not self.retrieve(settings.CORE_PROJECT):
            self.store(settings.CORE_PROJECT, type = 'internal')


class Project(
    provider.ProviderMixin,
    environment.EnvironmentModel
):
    remote = models.CharField(null=True, max_length=256)
    reference = models.CharField(null=True, max_length=128)

    class Meta:
        facade_class = ProjectFacade

    def get_provider_name(self):
        return 'project'
