
def get_queryset(instance, relation):
    is_list = isinstance(relation, (list, tuple))
    
    if not instance:
        return None
    
    if is_list and len(relation) > 1:
        return get_queryset(getattr(instance, relation[0]), relation[1:])
    else:
        relation = relation[0] if is_list else relation
        return getattr(instance, relation)
