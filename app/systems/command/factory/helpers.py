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
        if len(info) > 2:
            property = info[1]
            args = info[2:]
            getattr(command, "parse_{}".format(property))(*args)

def get_fields(command, fields):
    data = {}
    for name, info in fields.items():
        property = info[1]
        data[name] = getattr(command, property)
    return data 


def set_scopes(command, scopes):
    for name, info in scopes.items():
        getattr(command, "set_{}_scope".format(name))()
    
def get_scope(instance, scope_name, scopes):
    scope = getattr(instance, scope_name, None)
    if scope and isinstance(scope, AppModel):
        return scope.name
    else:
        for name, info in scopes.items():
            if name != scope_name:
                scope = getattr(instance, name, None)
                if scope and isinstance(scope, AppModel):
                    result_name = get_scope(scope, scope_name, scopes)
                    if result_name:
                        return result_name
    return None         


def exec_methods(instance, methods):
    for method, params in methods.items():
        method = getattr(instance, method)
        if not params:
            method()
        elif isinstance(params, dict):
            method(**params)
        else:
            method(*ensure_list(params))
