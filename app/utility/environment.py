from collections import OrderedDict
from django.conf import settings

from settings.config import Config
from utility.filesystem import load_yaml, save_yaml, remove_dir, remove_file
from utility.data import Collection, sorted_keys
from utility.time import Time

import os
import threading
import copy


class EnvironmentError(Exception):
    pass


class MetaEnvironment(type):

    def get_db_path(self, name = None):
        env_name = self.get_active_env() if name is None else name
        return "{}-{}.db".format(settings.BASE_DATA_PATH, env_name)

    def get_env_path(self):
        return "{}.env".format(settings.BASE_DATA_PATH)

    def get_module_path(self, name = None):
        env_name = self.get_active_env() if name is None else name
        return os.path.join(settings.MODULE_BASE_PATH, env_name)


    def load_data(self, reset = False):
        if reset or not self.data:
            save_data = False
            with self.lock:
                self.data = load_yaml(settings.RUNTIME_PATH)
                if self.data is None:
                    time = self.time.now
                    self.data = {
                        'active': settings.DEFAULT_ENV_NAME,
                        'environments': {
                            settings.DEFAULT_ENV_NAME: {
                                'repo': settings.DEFAULT_RUNTIME_REPO,
                                'base_image': settings.DEFAULT_RUNTIME_IMAGE,
                                'created': time,
                                'updated': time
                            }
                        }
                    }
                    save_data = True
                else:
                    for name, config in self.data['environments'].items():
                        self.data['environments'][name]['created'] = self.time.to_datetime(config['created'])
                        self.data['environments'][name]['updated'] = self.time.to_datetime(config['updated'])
            if save_data:
                self.save_data()

    def save_data(self):
        with self.lock:
            data = copy.deepcopy(self.data)

            for name, config in data['environments'].items():
                data['environments'][name]['created'] = self.time.to_string(config['created'])
                data['environments'][name]['updated'] = self.time.to_string(config['updated'])

            save_yaml(settings.RUNTIME_PATH, data, permissions = 0o664)


    def save_env_vars(self, name = None):
        self.load_data()

        env_name = self.get_active_env() if name is None else name
        variables = {}

        with self.lock:
            if env_name not in self.data['environments']:
                raise EnvironmentError("Environment {} is not defined".format(env_name))

            for field_name, field_value in self.data['environments'][env_name].items():
                variables["ZIMAGI_{}".format(field_name.upper())] = field_value

            Config.save(self.get_env_path(), variables)

    def delete_env_vars(self):
        with self.lock:
            Config.remove(self.get_env_path())


    def get_env_defaults(self):
        return {
            'repo': settings.DEFAULT_RUNTIME_REPO,
            'base_image': settings.DEFAULT_RUNTIME_IMAGE
        }


    def get_all_env(self):
        self.load_data()

        env_data = OrderedDict()
        with self.lock:
            env_names = sorted_keys(self.data['environments'], 'created')

        for env_name in env_names:
            env_data[env_name] = self.get_env(env_name)

        return env_data

    def get_env(self, name = None):
        self.load_data()

        env_name = self.get_active_env() if name is None else name

        with self.lock:
            if env_name not in self.data['environments']:
                raise EnvironmentError("Environment {} is not defined".format(env_name))

            env_data = copy.deepcopy(self.data['environments'][env_name])

        if not os.path.isfile(self.get_env_path()):
            env_data['runtime_image'] = None
            self.save_env(env_name, **env_data)

        env_data['name'] = env_name
        return Collection(**env_data)

    def save_env(self, name = None, **fields):
        self.load_data()

        active_env = self.get_active_env()
        env_name = active_env if name is None else name
        time = time = self.time.now
        defaults = self.get_env_defaults()

        with self.lock:
            if env_name not in self.data['environments']:
                self.data['environments'][env_name] = {}

            for field_name, field_value in fields.items():
                if field_name in defaults and field_value is None:
                    field_value = defaults[field_name]

                self.data['environments'][env_name][field_name] = field_value

            for field_name, default_value in defaults.items():
                if field_name not in self.data['environments'][env_name]:
                    self.data['environments'][env_name][field_name] = default_value

            if 'created' not in self.data['environments'][env_name]:
                self.data['environments'][env_name]['created'] = time

            self.data['environments'][env_name]['updated'] = time

        self.save_data()

        # Current environment is saved environment?
        if name is None or env_name == active_env:
            self.save_env_vars(env_name)

    def delete_env(self, name = None, remove_module_path = False):
        self.load_data()

        active_env = self.get_active_env()
        env_name = active_env if name is None else name

        with self.lock:
            # Current environment is deleted environment?
            if name is None or env_name == active_env:
                self.data['active'] = settings.DEFAULT_ENV_NAME

            if env_name != settings.DEFAULT_ENV_NAME:
                self.data['environments'].pop(env_name)
                remove_file(self.get_db_path(env_name))

                if remove_module_path:
                    remove_dir(self.get_module_path(env_name))

        self.save_data()

        # Current environment is deleted environment?
        if name is None or env_name == active_env:
            self.delete_env_vars()


    def get_active_env(self):
        self.load_data()
        with self.lock:
            return self.data['active']

    def set_active_env(self, name):
        self.load_data()
        with self.lock:
            if name not in self.data['environments']:
                raise EnvironmentError("Environment {} is not defined".format(name))
            self.data['active'] = name
        self.save_data()


class Environment(object, metaclass = MetaEnvironment):
    time = Time()
    lock = threading.Lock()
    data = {}
