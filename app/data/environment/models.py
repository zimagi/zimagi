from django.conf import settings
from django.db import models as django

from systems.models import fields, base, facade
from utility.runtime import Runtime


class EnvironmentFacade(facade.ModelFacade):

    def ensure(self, env, user):
        curr_env = self.get_env()
        if not self.retrieve(curr_env):
            self.store(curr_env)
  
    def get_env(self):
        return Runtime.get_env()

    def set_env(self, name = None, repo = None, image = None):
        Runtime.set_env(name, repo, image)

    def delete_env(self):
        Runtime.delete_env()


    def render(self, *fields, **filters):
        data = super().render(*fields, **filters)
        env = self.get_env()

        data[0] = ['active'] + data[0]

        for index in range(1, len(data)):
            record = data[index]
            if env and record[0] == env:
                data[index] = ['******'] + data[index]
            else:
                data[index] = [''] + data[index]

        return data


class Environment(base.AppModel):
    
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
