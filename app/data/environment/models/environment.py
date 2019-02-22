from django.conf import settings

from systems import models
from utility.runtime import Runtime


class EnvironmentFacade(models.ModelFacade):

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
            if env and record[0] == env.value:
                data[index] = ['******'] + data[index]
            else:
                data[index] = [''] + data[index]

        return data


class Environment(models.AppModel):
    
    name = models.CharField(primary_key=True, max_length=256)
    host = models.URLField(null=True)
    port = models.IntegerField(default=5123)
    token = models.EncryptedCharField(max_length=40, default=settings.DEFAULT_ADMIN_TOKEN)
    repo = models.CharField(max_length=1096, default=settings.DEFAULT_RUNTIME_REPO)
    image = models.CharField(max_length=256, default=settings.DEFAULT_RUNTIME_IMAGE)

    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
