from contextlib import contextmanager

import os
import threading
import pathlib
import shutil
import string
import random
import datetime


@contextmanager
def temp_dir(*args, **kwargs):
    temp = TempDir()
    try:
        yield temp
    finally:
        temp.delete()


class TempDir(object):

    def __init__(self):
        self.temp_name = self._generate_name()
        self.temp_path = "/tmp/{}".format(self.temp_name)

        self.thread_lock = threading.Lock()
        
        pathlib.Path(self.temp_path).mkdir(mode = 0o700, parents = True, exist_ok = True)

    def _generate_name(self, length = 5):
        chars = string.ascii_lowercase + string.digits
        random_text = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
        return "{}-{}".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"), random_text)


    def path(self, file_name, directory = None):
        if file_name.startswith(self.temp_path):
            return file_name
        
        if directory:
            temp_path = os.path.join(self.temp_path, directory)
            pathlib.Path(temp_path).mkdir(mode = 0o700, parents = True, exist_ok = True)
        else:
            temp_path = self.temp_path
        
        return os.path.join(temp_path, file_name)


    def load(self, file_name, directory = None, binary = False):
        tmp_path = self.path(file_name, directory = directory)
        operation = 'rb' if binary else 'r'
        content = None

        with self.thread_lock:        
            if os.path.exists(tmp_path):
                with open(tmp_path, operation) as file:
                    content = file.read()
        
        return content

    def save(self, content, name = None, directory = None, extension = None, binary = False):
        if name is None:
            name = self._generate_name()
        
        tmp_path = self.path(name, directory = directory)
        operation = 'wb' if binary else 'w'

        if extension:
            tmp_path = "{}.{}".format(tmp_path, extension)

        with self.thread_lock:
            with open(tmp_path, operation) as file:
                file.write(content)

            path = pathlib.Path(tmp_path)
            path.chmod(0o700)

        return tmp_path

    def link(self, source_path, name = None, directory = None):
        if name is None:
            file_name = self._generate_name()
        
        tmp_path = self.path(name, directory = directory)
        os.symlink(source_path, tmp_path)

    def delete(self):
        if self.temp_path.startswith('/tmp/'):
            shutil.rmtree(self.temp_path, ignore_errors = True)
