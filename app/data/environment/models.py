from django.conf import settings
from django.db import models as django

from systems.models import fields, base, resource, provider
from utility.runtime import Runtime


class EnvironmentFacade(
    provider.ProviderModelFacadeMixin,
    resource.ResourceModelFacadeMixin
):
    def get_packages(self):
        return [] # Do not export with db dumps!!

    def ensure(self, command):
        env_name = self.get_env()
        env = self.retrieve(env_name)

        if not env:
            env = command.environment_provider.create(env_name, {})

        if not Runtime.data:
            env.runtime_image = None
            env.save()

    def delete(self, key, **filters):
        pass


    def get_env(self):
        return Runtime.get_env()

    def set_env(self, name = None, repo = None, image = None):
        Runtime.set_env(name, repo, image)

    def delete_env(self):
        Runtime.delete_env()


    def get_field_is_active_display(self, instance, value, short):
        return self.dynamic_color(str(value))


class Environment(
    provider.ProviderMixin,
    resource.ResourceModel
):
    repo = django.CharField(max_length = 1096, default = settings.DEFAULT_RUNTIME_REPO)
    base_image = django.CharField(max_length = 256, default = settings.DEFAULT_RUNTIME_IMAGE)
    runtime_image = django.CharField(max_length = 256, null = True)

    class Meta(resource.ResourceModel.Meta):
        verbose_name = 'environment'
        verbose_name_plural = 'environments'
        facade_class = EnvironmentFacade
        dynamic_fields = ['is_active']
        ordering = ['name']
        provider_name = 'environment'

    def  __str__(self):
        return "{}".format(self.name)

    def get_id(self):
        return self.name

    @property
    def is_active(self):
        return True if self.name == self.facade.get_env() else False


    def save(self, *args, **kwargs):
        from data.state.models import State
        super().save(*args, **kwargs)

        env_name = Runtime.get_env()
        if self.name == env_name:
            image = self.base_image
            if self.runtime_image:
                image = self.runtime_image

            Runtime.set_env(
                self.name,
                self.repo,
                image
        )
        State.facade.store('env_ensure', value = True)
        State.facade.store('config_ensure', value = True)
