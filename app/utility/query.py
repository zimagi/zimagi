from .data import ensure_list

import copy


def get_queryset(instance, relation):
    is_list = isinstance(relation, (list, tuple))

    if not instance:
        return None

    if is_list and len(relation) > 1:
        return get_queryset(getattr(instance, relation[0]), relation[1:])
    else:
        relation = relation[0] if is_list else relation
        return getattr(instance, relation)


def init_fields(fields, default = None, remove = None):
    if default is None:
        default = []
    elif not fields:
        default = copy.deepcopy(default)

    fields = copy.deepcopy(ensure_list(fields)) if fields else default

    if remove:
        remove = ensure_list(remove)
        fields = [field for field in fields if field not in remove]

    return fields

def init_filters(filters, default = None):
    if default is None:
        default = {}
    elif not filters:
        default = copy.deepcopy(default)

    return copy.deepcopy(filters) if filters else default
