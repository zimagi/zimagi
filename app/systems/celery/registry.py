from importlib import import_module

from celery._state import get_current_app
from celery.app.registry import TaskRegistry

import copy


class CommandTaskRegistry(TaskRegistry):

    def __getitem__(self, name):
        return copy.deepcopy(super().__getitem__(name))

    def get(self, name, default = None):
        if default is not None and name not in self:
            return default
        return self.__getitem__(name)

    def get_original(self, name):
        return super().__getitem__(name)


def _unpickle_task(name, module = None):
    if module:
        import_module(module)
    return get_current_app().tasks.get_original(name)
