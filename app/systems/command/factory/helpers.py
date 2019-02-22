from systems import models
from utility.data import ensure_list


def get_value(value, default):
    return value if value is not None else default

def get_facade(name, base_name):
    return get_value(name, "_{}".format(base_name))

def get_joined_value(value, *args):
    return get_value(value, "_".join([ x for x in args if x is not None ]))


def parse_scopes(command, scopes):
    for name, info in scopes.items():
        if isinstance(info, (tuple, list, str)):
            args = ensure_list(info)
            kwargs = {}
        else:
            args = []
            kwargs = info
            
        getattr(command, "parse_{}_name".format(name))(*args, **kwargs)

def set_scopes(command, scopes):
    for scope in scopes:
        getattr(command, "set_{}_scope".format(scope))()
    
def get_scope(instance, scope_name, scopes):
    scope = getattr(instance, scope_name, None)
    if scope and isinstance(scope, models.AppModel):
        return scope.name
    else:
        for name, info in scopes.items():
            if name != scope_name:
                scope = getattr(instance, name, None)
                if scope and isinstance(scope, models.AppModel):
                    result_name = get_scope(scope, scope_name, scopes)
                    if result_name:
                        return result_name
    return None         
