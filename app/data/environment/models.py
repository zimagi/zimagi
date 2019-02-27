from django.conf import settings
from django.db import models as django

from systems.models import fields, base, facade, provider
from utility.runtime import Runtime


class EnvironmentFacade(
    provider.ProviderModelFacadeMixin,
    facade.ModelFacade
):
    def ensure(self, command):
        curr_env = self.get_env()
        if not self.retrieve(curr_env):
            command.env_provider.create(curr_env, {})

    def get_provider_name(self):
        return 'env'

  
    def get_env(self):
        return Runtime.get_env()

    def set_env(self, name = None, repo = None, image = None):
        Runtime.set_env(name, repo, image)

    def delete_env(self):
        Runtime.delete_env()


    def render(self, *fields, **filters):
        data = super().render(*fields, **filters)
        env = self.get_env()

        data[0] = ['Active'] + data[0]

        for index in range(1, len(data)):
            record = data[index]
            if env and record[0] == env:
                data[index] = ['******'] + data[index]
            else:
                data[index] = [''] + data[index]

        return data
    
    def default_order(self):
        return 'name'

    def get_display_fields(self):
        return (
            'name',
            'host', 
            'port',
            '---',
            'user',
            'token',
            '---', 
            'repo',
            'image',
            '---',
            'created',
            'updated'
        )
    
    def get_field_name_display(self, value):
        return ('Name', value)
    
    def get_field_host_display(self, value):
        return ('Host', value)
    
    def get_field_port_display(self, value):
        return ('Port', value)
    
    def get_field_user_display(self, value):
        return ('User', value)
    
    def get_field_token_display(self, value):
        return ('Token', value[:10] + '...')
    
    def get_field_repo_display(self, value):
        return ('Repository', value)
    
    def get_field_image_display(self, value):
        return ('Image', value)


class Environment(
    provider.ProviderMixin,
    base.AppModel
):    
    name = django.CharField(primary_key=True, max_length=256)
    host = django.URLField(null=True)
    port = django.IntegerField(default=5123)
    user = django.CharField(max_length=150, default=settings.ADMIN_USER)
    token = fields.EncryptedCharField(max_length=256, default=settings.DEFAULT_ADMIN_TOKEN)
    repo = django.CharField(max_length=1096, default=settings.DEFAULT_RUNTIME_REPO)
    image = django.CharField(max_length=256, default=settings.DEFAULT_RUNTIME_IMAGE)

    class Meta(base.AppModel.Meta):
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
