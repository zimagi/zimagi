from django.conf import settings

import os
import shutil
import threading
import json


class Config(object):

    @classmethod
    def value(cls, name, default = None):
        # Order of precedence
        # 1. Local environment variable if it exists
        # 2. Default value provided

        value = default

        # Check for an existing environment variable
        try:
            value = os.environ[name]
        except:
            pass

        return value

    @classmethod
    def boolean(cls, name, default = False):
        return json.loads(cls.value(name, str(default)).lower())

    @classmethod
    def integer(cls, name, default = 0):
        return int(cls.value(name, default))

    @classmethod
    def decimal(cls, name, default = 0):
        return float(cls.value(name, default))

    @classmethod
    def string(cls, name, default = ''):
        return str(cls.value(name, default))

    @classmethod
    def list(cls, name, default = []):
        if not cls.value(name, None):
            return default
        return [x.strip() for x in cls.string(name).split(',')]

    @classmethod
    def dict(cls, name, default = {}):
        value = cls.value(name, default)

        if isinstance(value, str):
            value = json.loads(value)

        return value


    @classmethod
    def load(cls, path, default = {}):
        data = default

        if os.path.exists(path):
            with open(path, 'r') as file:
                data = {}
                for statement in file.read().split("\n"):
                    statement = statement.strip()

                    if statement and statement[0] != '#':
                        (variable, value) = statement.split("=")
                        data[variable] = value
        return data

    @classmethod
    def save(cls, path, data):
        with open(path, 'w') as file:
            statements = []
            for variable, value in data.items():
                statements.append("{}={}".format(variable.upper(), value))

            file.write("\n".join(statements))

    @classmethod
    def variable(cls, scope, name):
        return "{}_{}".format(scope.upper(), name.upper())


class RuntimeConfig(object):

    lock = threading.Lock()
    config = {}

    @classmethod
    def save(cls, name, value):
        with cls.lock:
            cls.config[name] = value
            return cls.config[name]

    @classmethod
    def get(cls, name, default = None):
        with cls.lock:
            if name not in cls.config:
                return default
            else:
                return cls.config[name]


    @classmethod
    def api(cls, value = None):
        if value is not None:
            return cls.save('api', value)
        return cls.get('api')

    @classmethod
    def debug(cls, value = None):
        if value is not None:
            return cls.save('debug', value)
        return cls.get('debug', settings.DEBUG)

    @classmethod
    def parallel(cls, value = None):
        if value is not None:
            return cls.save('parallel', value)
        return cls.get('parallel', settings.PARALLEL)

    @classmethod
    def color(cls, value = None):
        if value is not None:
            return cls.save('color', value)
        return cls.get('color', settings.DISPLAY_COLOR)

    @classmethod
    def width(cls, value = None):
        if value is not None:
            return cls.save('width', value)

        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        return cls.get('width', columns)
