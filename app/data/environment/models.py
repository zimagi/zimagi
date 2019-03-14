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
        curr_env = self.retrieve(env_name)
        if not curr_env:
            curr_env = command.env_provider.create(env_name, {})

        Runtime.curr_env(curr_env)

    def keep(self):
        return self.get_env()

    def get_provider_name(self):
        return 'env'

    def get_children(self):
        return (
            # 'federation',
            'network',
            'project',
            'config',
            'group'
        )


    def get_env(self):
        return Runtime.get_env()

    def get_env_id(self):
        return Runtime.curr_env().id

    def set_env(self, name = None, repo = None, image = None):
        Runtime.set_env(name, repo, image)

    def delete_env(self):
        Runtime.delete_env()


    def default_order(self):
        return 'name'

    def get_list_fields(self):
        return (
            ('name', 'Name'),
            ('active', 'Active'),
            ('type', 'Type'),
            ('host', 'Host'),
            ('port', 'Port'),
            ('user', 'User'),
            ('token', 'Token'),
            ('repo', 'Registry'),
            ('base_image', 'Base image'),
            ('runtime_image', 'Runtime image')
        )

    def get_display_fields(self):
        return (
            ('name', 'Name'),
            ('active', 'Active'),
            ('type', 'Type'),
            ('host', 'Host'),
            ('port', 'Port'),
            '---',
            ('user', 'User'),
            ('token', 'Token'),
            '---',
            ('repo', 'Registry'),
            ('base_image', 'Base image'),
            ('runtime_image', 'Runtime image'),
            '---',
            ('created', 'Created'),
            ('updated', 'Updated')
        )

    def get_field_name_display(self, instance, value, short):
        return value

    def get_field_host_display(self, instance, value, short):
        return value

    def get_field_port_display(self, instance, value, short):
        return value

    def get_field_user_display(self, instance, value, short):
        return value

    def get_field_token_display(self, instance, value, short):
        if short:
            return value[:10] + '...'
        else:
            return value

    def get_field_repo_display(self, instance, value, short):
        return value

    def get_field_image_display(self, instance, value, short):
        return value

    def get_field_active_display(self, instance, value, short):
        if instance.name == self.get_env():
            return '******'
        return ''


class Environment(
    provider.ProviderMixin,
    resource.ResourceModel
):
    host = django.URLField(null=True)
    port = django.IntegerField(default=5123)
    user = django.CharField(max_length=150, default=settings.ADMIN_USER)
    token = fields.EncryptedCharField(max_length=256, default=settings.DEFAULT_ADMIN_TOKEN)
    repo = django.CharField(max_length=1096, default=settings.DEFAULT_RUNTIME_REPO)
    base_image = django.CharField(max_length=256, default=settings.DEFAULT_RUNTIME_IMAGE)
    runtime_image = django.CharField(max_length=256, null=True)

    class Meta(resource.ResourceModel.Meta):
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)

    def get_id_fields(self):
        return ['name']

    def save(self, *args, **kwargs):
        env_name = Runtime.get_env()

        if self.name == env_name:
            image = self.base_image
            if self.runtime_image:
                image = self.runtime_image
            Runtime.set_env(self.name, self.repo, image)

        super().save(*args, **kwargs)

