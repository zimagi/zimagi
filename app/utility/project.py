from contextlib import contextmanager

from django.conf import settings

from .runtime import Runtime
from .filesystem import FileSystem


@contextmanager
def project_dir(*args, **kwargs):
    project = ProjectDir()
    yield project


class ProjectDir(FileSystem):

    def __init__(self, type, name):
        self.type = type
        self.name = name
        super().__init__("{}/{}/{}/{}".format(
            settings.LIB_DIR,
            Runtime.get_env(),
            self.type,
            self.name
        ))
