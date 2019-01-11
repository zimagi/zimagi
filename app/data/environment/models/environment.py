from django.conf import settings

from systems import models
from systems.db.manager import DatabaseState, DatabaseManager
from data.environment.models import State
from utility.config import Config

import os


class EnvironmentFacade(models.ModelFacade):

    def __init__(self, cls):
        super().__init__(cls)
        
        self.fields.extend(['repo', 'image'])
        self.optional.extend(['repo', 'image'])


    def get_packages(self):
        return super().get_packages() + ['environment', 'config', 'server']


    @property
    def default_env_name(self):
        return 'default'

    def ensure(self, env, user):
        curr_env = self.get_env()

        if not curr_env:
            if not self.retrieve(self.default_env_name):
                self.store(self.default_env_name, 
                    repo = self.get_repo_name(self.default_env_name), 
                    image = self.get_image_name(self.default_env_name)
                )
            self.set_env()


    def get_env(self):
        return settings.RUNTIME_ENV.get('CENV_ENV', '').lower()

    def set_env(self, name = None, repo = None, image = None):
        if name is None:
            name = self.default_env_name

        if repo is None:
            repo = self.get_repo_name(name)

        if image is None:
            image = self.get_image_name(name)

        settings.RUNTIME_ENV['CENV_ENV'] = name.upper()
        settings.RUNTIME_ENV[Config.variable(name, 'REPO')] = repo
        settings.RUNTIME_ENV[Config.variable(name, 'IMAGE')] = image

        return name

    def delete_env(self, name = None):
        curr_env = self.get_env()
        set_env = False

        if name is None or name == curr_env:
            name = curr_env
            set_env = True
        
        settings.RUNTIME_ENV.pop(Config.variable(name, 'REPO'))
        settings.RUNTIME_ENV.pop(Config.variable(name, 'IMAGE'))

        env_names = settings.RUNTIME_ENV['CENV_ENV_NAMES'].split(',')
        env_names.remove(name.upper())
        settings.RUNTIME_ENV['CENV_ENV_NAMES'] = ",".join(env_names)

        if set_env:
            DatabaseState.mark_remove()
            return self.set_env()
        else:
            file_path = DatabaseManager().get_env_path(name)
            os.remove(file_path)        
            return True

    
    def get_repo_name(self, key):
        return settings.RUNTIME_ENV.get(Config.variable(key, 'REPO'), '')

    def get_image_name(self, key):
        return settings.RUNTIME_ENV.get(Config.variable(key, 'IMAGE'), settings.DEFAULT_RUNTIME_IMAGE)


    def retrieve(self, key, **filters):
        data = super().retrieve(key, **filters)
        if data:
            data.repo = self.get_repo_name(key)
            data.image = self.get_image_name(key)
        
        return data

    def store(self, key, **values):
        repo_name = Config.variable(key, 'REPO')
        image_name = Config.variable(key, 'IMAGE')

        if 'CENV_ENV_NAMES' not in settings.RUNTIME_ENV:
            settings.RUNTIME_ENV['CENV_ENV_NAMES'] = key.upper()
        else:
            keys = settings.RUNTIME_ENV['CENV_ENV_NAMES'].split(',')
            if key.upper() not in keys:
                keys.append(key.upper())
            
            settings.RUNTIME_ENV['CENV_ENV_NAMES'] = ",".join(keys)            

        if 'repo' in values or repo_name not in settings.RUNTIME_ENV:
            settings.RUNTIME_ENV[repo_name] = values.pop('repo', '')
        
        if 'image' in values or image_name not in settings.RUNTIME_ENV:
            settings.RUNTIME_ENV[image_name] = values.pop('image', settings.DEFAULT_RUNTIME_IMAGE)

        instance, created = super().store(key, **values)
        instance.repo = settings.RUNTIME_ENV[repo_name]
        instance.image = settings.RUNTIME_ENV[image_name]

        return (instance, created)


    def render(self, fields, queryset_values):
        env = self.get_env()
        data = [['active'] + list(fields) + ['repo', 'image']]

        for env_name in settings.RUNTIME_ENV['CENV_ENV_NAMES'].split(','):
            env_name = env_name.lower()
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

            record.extend([
                self.get_repo_name(env_name),
                self.get_image_name(env_name)
            ])
            data.append(record)

        return data


class Environment(models.AppModel):
    
    name = models.CharField(primary_key=True, max_length=256)
    host = models.URLField(null=True)
    port = models.IntegerField(null=True, default=5123)
    
    user = models.CharField(null=True, max_length=40, default='admin')
    token = models.CharField(null=True, max_length=40, default=settings.DEFAULT_ADMIN_TOKEN)

    class Meta:
        facade_class = EnvironmentFacade

    def  __str__(self):
        return "{}".format(self.name)
