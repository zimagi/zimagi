from contextlib import contextmanager

import os
import pathlib
import shutil
import threading
import oyaml


def load_file(file_path):
    content = None
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
    return content

def load_yaml(file_path):
    content = load_file(file_path)
    if content:
        content = oyaml.safe_load(content)
    return content


@contextmanager
def filesystem_dir(base_path):
    directory = FileSystem(base_path)
    yield directory


class FileSystem(object):

    thread_lock = threading.Lock()


    def __init__(self, base_path):
        self.base_path = base_path
        pathlib.Path(self.base_path).mkdir(mode = 0o700, parents = True, exist_ok = True)


    def mkdir(self, directory):
        path = os.path.join(self.base_path, directory)
        pathlib.Path(path).mkdir(mode = 0o700, parents = True, exist_ok = True)
        return path


    def path(self, file_name, directory = None):
        if file_name.startswith(self.base_path):
            return file_name

        if directory:
            path = self.mkdir(directory)
        else:
            path = self.base_path

        return os.path.join(path, file_name)

    def exists(self, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.exists(path):
            return True
        return False


    def load(self, file_name, directory = None, binary = False):
        path = self.path(file_name, directory = directory)
        operation = 'rb' if binary else 'r'
        content = None

        with self.thread_lock:
            if os.path.exists(path):
                with open(path, operation) as file:
                    content = file.read()

        return content

    def save(self, content, name, directory = None, extension = None, binary = False):
        path = self.path(name, directory = directory)
        operation = 'wb' if binary else 'w'

        if extension:
            path = "{}.{}".format(path, extension)

        with self.thread_lock:
            with open(path, operation) as file:
                file.write(content)

            path_obj = pathlib.Path(path)
            path_obj.chmod(0o700)

        return path

    def link(self, source_path, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.isfile(path):
            os.remove(path)
        os.symlink(source_path, path)
        return path

    def copy(self, source_path, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.isfile(path):
            os.remove(path)
        shutil.copy(source_path, path)
        return path

    def remove(self, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if path.startswith(self.base_path):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors = True)
            elif os.path.isfile(path):
                os.remove(path)

    def delete(self):
        shutil.rmtree(self.base_path, ignore_errors = True)
