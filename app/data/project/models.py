from django.conf import settings
from django.db import models as django

from settings import Roles
from systems.models import environment, group, provider


class ProjectFacade(
    provider.ProviderModelFacadeMixin,
    group.GroupModelFacadeMixin,
    environment.EnvironmentModelFacadeMixin
):
    def ensure(self, command):
        if not self.retrieve(settings.CORE_PROJECT):
            command.project_provider.create(settings.CORE_PROJECT, {})

    def get_provider_name(self):
        return 'project'


class Project(
    provider.ProviderMixin,
    group.GroupMixin,
    environment.EnvironmentModel
):
    remote = django.CharField(null=True, max_length=256)
    reference = django.CharField(null=True, max_length=128)

    class Meta(environment.EnvironmentModel.Meta):
        facade_class = ProjectFacade

    def allowed_groups(self):
        return [ Roles.admin ]
