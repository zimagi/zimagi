from ..errors import RestrictedError
from utility.data import ensure_list, normalize_dict


class ModelFacadeUpdateMixin(object):

    def create(self, key, **values):
        values[self.key()] = key
        self._check_scope(values)
        return self.model(**values)

    def get_or_create(self, key):
        instance = self.retrieve(key)
        if not instance:
            instance = self.create(key)
        return instance


    def store(self, key, **values):
        filters = { self.key(): key }
        instance = self.retrieve(key, **filters)
        created = False

        if not instance:
            instance = self.create(key, **filters)
            created = True

        values = normalize_dict(values)

        for field, value in values.items():
            setattr(instance, field, value)

        instance.save()
        return (instance, created)


    def delete(self, key, **filters):
        if key not in ensure_list(self.keep(key)):
            filters[self.key()] = key
            return self.clear(**filters)
        else:
            raise RestrictedError("Removal of {} {} is restricted".format(self.model.__name__.lower(), key))

    def clear(self, **filters):
        queryset  = self.filter(**filters)
        keep_list = self.keep()
        if keep_list:
            queryset = queryset.exclude(**{
                "{}__in".format(self.key()): ensure_list(keep_list)
            })

        deleted, del_per_type = queryset.delete()
        if deleted:
            return True
        return False
