import os
from contextlib import contextmanager

from django.conf import settings

from .filesystem import FileSystem


@contextmanager
def project_dir(type, name=None, base_path=None):
    project = ProjectDir(type, name, base_path)
    yield project


@contextmanager
def project_temp_dir(type, name=None, base_path=None):
    project = ProjectDir(type, name, base_path)
    try:
        yield project
    finally:
        project.delete()


class ProjectDir(FileSystem):
    def __init__(self, type, name=None, base_path=None):
        self.type = type
        self.name = name

        if base_path is None:
            base_path = settings.MANAGER.file_path

        path_args = [base_path, self.type]
        if self.name:
            path_args.append(self.name)

        super().__init__(os.path.join(*path_args))
