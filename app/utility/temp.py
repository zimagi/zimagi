import datetime
import random
import string
from contextlib import contextmanager

from .filesystem import FileSystem


@contextmanager
def temp_dir():
    temp = TempDir()
    try:
        yield temp
    finally:
        temp.delete()


class TempDir(FileSystem):
    def __init__(self):
        self.name = self._generate_name()
        super().__init__(f"/tmp/{self.name}")

    def _generate_name(self, length=5):
        chars = string.ascii_lowercase + string.digits
        random_text = "".join(random.SystemRandom().choice(chars) for _ in range(length))
        return "{}-{}".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"), random_text)

    def save(self, content, name=None, directory=None, **kwargs):
        if name is None:
            name = self._generate_name()
        return super().save(content, name, directory, **kwargs)

    def link(self, source_path, name=None, directory=None):
        if name is None:
            name = self._generate_name()
        return super().link(source_path, name, directory)
