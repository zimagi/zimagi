import os
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
