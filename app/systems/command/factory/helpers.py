from systems.models.base import AppModel
from utility.data import ensure_list


def get_value(value, default):
    return value if value is not None else default

def get_facade(name, base_name):
    return get_value(name, "_{}".format(base_name))

def get_joined_value(value, *args):
    return get_value(value, "_".join([ x for x in args if x is not None ]))


def parse_fields(command, fields):
    for name, info in fields.items():
        getattr(command, "parse_{}".format(info[0]))(*info[1:])

def get_fields(command, fields):
    data = {}
    for name, info in fields.items():
        data[name] = getattr(command, info[0])
    return data 


def exec_methods(instance, methods):
    for method, params in methods.items():
        method = getattr(instance, method)
        if not params:
            method()
        elif isinstance(params, dict):
            method(**params)
        else:
            method(*ensure_list(params))
