from utility.data import serialized_token, unserialize, normalize_value, load_json
from utility.filesystem import load_file, save_file, remove_file

import os


class Config(object):

    @classmethod
    def value(cls, name, default = None, default_on_empty = False):
        # Order of precedence
        # 1. Local environment variable if it exists
        # 2. Default value provided

        value = default

        # Check for an existing environment variable
        try:
            value = os.environ[name]
        except:
            pass

        if value and isinstance(value, str) and value.startswith(serialized_token()):
            value = unserialize(value[len(serialized_token()):])

        if not value and default_on_empty:
            value = default

        return value

    @classmethod
    def boolean(cls, name, default = False):
        return load_json(cls.value(name, str(default)).lower())

    @classmethod
    def integer(cls, name, default = 0):
        return int(cls.value(name, default, default_on_empty = True))

    @classmethod
    def decimal(cls, name, default = 0):
        return float(cls.value(name, default, default_on_empty = True))

    @classmethod
    def string(cls, name, default = '', default_on_empty = False):
        return str(cls.value(name, default, default_on_empty = default_on_empty))

    @classmethod
    def list(cls, name, default = None):
        if not default:
            default = []

        value = cls.value(name, None, default_on_empty = True)
        if not value:
            return default

        if isinstance(value, str):
            value = load_json(value)

        return value

    @classmethod
    def dict(cls, name, default = None):
        if not default:
            default = {}

        value = cls.value(name, default, default_on_empty = True)

        if isinstance(value, str):
            value = load_json(value)

        return value


    @classmethod
    def load(cls, path, default = None):
        if not default:
            default = {}

        data = default

        if os.path.exists(path):
            data = {}
            for statement in load_file(path).split("\n"):
                statement = statement.strip()

                if statement and statement[0] != '#':
                    (variable, value) = statement.split("=")
                    data[variable] = normalize_value(value)
        return data

    @classmethod
    def save(cls, path, data):
        statements = []
        for variable, value in data.items():
            statements.append('{}="{}"'.format(variable.upper(), value))

        save_file(path, "\n".join(statements), permissions = 0o644)

    @classmethod
    def remove(cls, path):
        remove_file(path)


    @classmethod
    def variable(cls, scope, name):
        return "{}_{}".format(scope.upper(), name.upper())
