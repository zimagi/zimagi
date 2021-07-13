from contextlib import contextmanager

from django.conf import settings

from .environment import Environment
from .filesystem import FileSystem


@contextmanager
def project_dir(type, name):
    project = ProjectDir(type, name)
    yield project


class ProjectDir(FileSystem):

    def __init__(self, type, name):
        self.type = type
        self.name = name
        super().__init__("{}/{}/{}/{}".format(
            settings.LIB_DIR,
            self.type,
            Environment.get_active_env(),
            self.name
        ))
