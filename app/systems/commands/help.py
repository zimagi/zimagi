from django.conf import settings

from utility.data import deep_merge

import threading
import os
import yaml
import re


class CommandDescriptions(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self.thread_lock = threading.Lock()
            self.load()
            self._initialized = True


    def load(self):
        self.descriptions = {}

        def load_inner(data, help_path):
            for name in os.listdir(help_path):
                path = os.path.join(help_path, name)
                if os.path.isfile(path):
                    if path.endswith('.yml'):
                        with open(path, 'r') as file:
                            file_data = yaml.safe_load(file.read())
                            deep_merge(data, file_data)
                else:
                    load_inner(data, path)

        with self.thread_lock:
            for help_dir in settings.MANAGER.index.help_search_path():
                load_inner(self.descriptions, help_dir)

    def get(self, full_name, overview = True):
        with self.thread_lock:
            components = re.split(r'\s+', full_name)
            component_length = len(components)
            scope = self.descriptions

            for index, component in enumerate(components):
                if component in scope:
                    if index + 1 == component_length:  # last component
                        text = scope[component].get('overview', ' ')
                        if not overview:
                            text += '\n' + scope[component].get('description', ' ')
                        return text
                    else:
                        scope = scope[component]
        return ' '
