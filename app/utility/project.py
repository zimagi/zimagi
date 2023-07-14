from contextlib import contextmanager
from django.conf import settings

from .filesystem import FileSystem
from .environment import Environment

import os


@contextmanager
def project_dir(type, name = None, base_path = None, env = False):
    project = ProjectDir(type, name, base_path, env)
    yield project

@contextmanager
def project_temp_dir(type, name = None, base_path = None, env = False):
    project = ProjectDir(type, name, base_path, env)
    try:
        yield project
    finally:
        project.delete()


class ProjectDir(FileSystem):

    def __init__(self, type, name = None, base_path = None, env = False):
        self.type = type
        self.name = name

        if base_path is None:
            base_path = settings.MANAGER.self.file_path

        path_args = [ base_path, self.type ]
        if env:
            path_args.append(Environment.get_active_env())
        if self.name:
            path_args.append(self.name)

        super().__init__(os.path.join(*path_args))
