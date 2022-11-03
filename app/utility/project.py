from contextlib import contextmanager
from django.conf import settings

from .filesystem import FileSystem


@contextmanager
def project_dir(type, name):
    project = ProjectDir(type, name)
    yield project

@contextmanager
def project_temp_dir(type, name):
    project = ProjectDir(type, name)
    try:
        yield project
    finally:
        project.delete()


class ProjectDir(FileSystem):

    def __init__(self, type, name):
        self.type = type
        self.name = name
        super().__init__("{}/{}/{}".format(
            settings.MANAGER.lib_path,
            self.type,
            self.name
        ))
