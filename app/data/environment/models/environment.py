from django.conf import settings

from systems import models
from utility.runtime import Runtime

import os


class EnvironmentFacade(models.ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)

        self.fields.extend(['repo', 'image'])
        self.optional.extend(['repo', 'image'])


    def get_packages(self):
        return super().get_packages() + ['environment', 'config', 'server']


    def ensure(self, env, user):
        curr_env = self.get_env()
        
        if not self.retrieve(curr_env):
            self.store(curr_env)
            
        self.set_env(curr_env)


    def get_env(self):
        return Runtime.get_env()

    def set_env(self, name = None, repo = None, image = None):
        return Runtime.set_env(name, repo, image)

    def delete_env(self, name = None):
        return Runtime.delete_env(name)


    def render(self, fields, queryset_values):
        env = self.get_env()
        fields = list(fields)
        data = [['Active'] + fields + ['Repo', 'Image']]
        
        fields.extend(['repo', 'image'])

        for env_name in Runtime.get_env_index():
            instance = self.retrieve(env_name)
            record = []

            if env and env_name == env:
                record.append('******')
            else:
                record.append('')

            for field in fields:
                if field == 'name':
                    record.append(env_name)
                else:
                    record.append(getattr(instance, field, ''))
        
            data.append(record)

        return data


class Environment(models.AppModel):
    
    name = models.CharField(primary_key=True, max_length=256)
    host = models.URLField(null=True)
    port = models.IntegerField(null=True, default=5123)
    
    token = models.CharField(null=True, max_length=40, default=settings.DEFAULT_ADMIN_TOKEN)

    @property
    def repo(self):
        return Runtime.get_repo_name(self.name)

    @repo.setter
    def repo(self, value):
        Runtime.set_repo_name(self.name, value)

    @property
    def image(self):
        return Runtime.get_image_name(self.name)

    @image.setter
    def image(self, value):
        Runtime.set_image_name(self.name, value)


    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)


    def save(self, *args, **kwargs):
        Runtime.add_env_index(self.name)
        return super().save(*args, **kwargs)
