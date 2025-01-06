import os
import random
import string

from systems.plugins.index import BasePlugin
from utility.data import ensure_list
from utility.text import Template


class TaskResult:
    def __init__(self, type):
        self.type = type
        self.data = None
        self.message = None

    def __str__(self):
        return f"[{self.type}]"


class BaseProvider(BasePlugin("task")):
    def __init__(self, type, name, command, module, config):
        super().__init__(type, name, command)

        self.module = module
        self.config = self.command.options.interpolate(config)

        self.roles = self.config.pop("roles", None)
        self.module_override = self.config.pop("module", None)

    def check_access(self):
        if self.roles:
            if not self.command.check_access_by_groups(self.module.instance, self.roles):
                return False
        return True

    def get_fields(self):
        # Override in subclass
        return {}

    def exec(self, params=None):
        results = TaskResult(self.name)
        if not params:
            params = {}

        if self.check_access():
            self.execute(results, params)
        else:
            self.command.error(f"Access is denied for task {self.name}")

        return results

    def execute(self, results, params):
        # Override in subclass
        pass

    def get_path(self, path):
        return os.path.join(self.get_module_path(), path)

    def get_module(self):
        return self.module.instance

    def get_module_path(self):
        instance = self.get_module()
        if self.module_override:
            instance = self.command.get_instance(instance.facade, self.module_override)
        return instance.provider.module_path(instance.name)

    def generate_name(self, length=32):
        chars = string.ascii_lowercase + string.digits
        return "".join(random.SystemRandom().choice(chars) for _ in range(length))

    def _merge_options(self, options, overrides, lock=False):
        if not lock and overrides:
            return {**options, **overrides}
        return options

    def _interpolate(self, value, variables):
        if value is None:
            return None

        final_value = []
        variables = self.command.options.interpolate(variables)

        for component in ensure_list(value):
            parser = Template(component)
            final_value.append(parser.substitute(**variables).strip())

        return final_value
