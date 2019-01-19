from django.conf import settings

from systems.db.manager import DatabaseState, DatabaseManager
from utility.config import Config

import os


class MetaRuntime(type):

    def get_env(self):
        return self.data.get('CENV_ENV', self.get_default_env_name())

    def set_env(self, name = None, repo = None, image = None):
        if name is None:
            name = self.get_default_env_name()

        if repo is None:
            repo = self.get_repo_name(name)

        if image is None:
            image = self.get_image_name(name)

        self.data['CENV_ENV'] = name
        self.set_repo_name(name, repo)
        self.set_image_name(name, image)

        return name

    def delete_env(self, name = None):
        curr_env = self.get_env()
        set_env = False

        if name is None or name == curr_env:
            name = curr_env
            set_env = True
        
        self.set_repo_name(name, None)
        self.set_image_name(name, None)
        self.delete_env_index(name)

        if set_env:
            DatabaseState.mark_remove()
            return self.set_env()
        else:
            file_path = DatabaseManager().get_env_path(name)
            os.remove(file_path)        
            return True

    def update_env(self, name, repo = None, image = None):
        if repo:
            self.set_repo_name(name, repo)
        if image:
            self.set_image_name(name, image)
        
        self.add_env_index(name)


    def load(self, env_path):
        self.data = Config.load(env_path, {})

        if 'CENV_ENV_NAMES' not in self.data:
            self.data['CENV_ENV_NAMES'] = []
        else:
            self.data['CENV_ENV_NAMES'] = self.data['CENV_ENV_NAMES'].split(',')

    def save(self, env_path):
        self.data['CENV_ENV_NAMES'] = ",".join(self.data['CENV_ENV_NAMES'])
        
        curr_env = self.data['CENV_ENV']
        self.set_repo_name(curr_env, self.get_repo_name(curr_env))
        self.set_image_name(curr_env, self.get_image_name(curr_env))
        
        Config.save(env_path, self.data)


    def get_env_index(self):
        return self.data.get('CENV_ENV_NAMES', [])
    

    def get_default_env_name(self):
        return settings.DEFAULT_ENV_NAME

    def get_repo_name(self, name = None):
        if not name:
            name = self.get_default_env_name()
        
        return self.data.get(Config.variable(name, 'REPO'), '')

    def set_repo_name(self, name, value):
        variable = Config.variable(name, 'REPO')

        if value is not None:
            self.data[variable] = value
        else:
            self.data.pop(variable, None)

    def get_image_name(self, name = None):
        if not name:
            name = self.get_default_env_name()
        
        return self.data.get(Config.variable(name, 'IMAGE'), 
            settings.DEFAULT_RUNTIME_IMAGE
        )

    def set_image_name(self, name, value):
        variable = Config.variable(name, 'IMAGE')

        if value is not None:
            self.data[variable] = value
        else:
            self.data.pop(variable, None)


    def add_env_index(self, name):
        if name not in self.data['CENV_ENV_NAMES']:
            self.data['CENV_ENV_NAMES'].append(name)

    def delete_env_index(self, name):
        self.data['CENV_ENV_NAMES'].remove(name)


class Runtime(object, metaclass = MetaRuntime):
    data = {}