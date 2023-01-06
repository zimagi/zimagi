from contextlib import contextmanager
from django.conf import settings

from .filesystem import FileSystem

import os


@contextmanager
def project_dir(type, name = None):
    project = ProjectDir(type, name)
    yield project

@contextmanager
def project_temp_dir(type, name = None):
    project = ProjectDir(type, name)
    try:
        yield project
    finally:
        project.delete()


class ProjectDir(FileSystem):

    def __init__(self, type, name = None):
        self.type = type
        self.name = name

        if name:
            path = os.path.join(
                settings.MANAGER.lib_path,
                self.type,
                self.name
            )
        else:
            path = os.path.join(
                settings.MANAGER.lib_path,
                self.type
            )
        super().__init__(path)
