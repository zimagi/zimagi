import copy
import re

from utility import data


class QueryMixin:
    def facade(self, facade, use_cache=True):
        result = None

        if use_cache and getattr(self, "_facade_cache", None) is None:
            self._facade_cache = {}

        if not isinstance(facade, str):
            name = facade.name
        else:
            name = facade
            facade = self.manager.index.get_facade_index()[name]

        if use_cache and not self._facade_cache.get(name, None):
            self._facade_cache[name] = copy.deepcopy(facade)
        else:
            result = copy.deepcopy(facade)

        return self._facade_cache[name] if use_cache else result

    def _init_instance_cache(self, facade):
        cache_variable = f"_data_{facade.name}_cache"

        if not getattr(self, cache_variable, None):
            setattr(self, cache_variable, {})

        return cache_variable

    def _get_cache_instance(self, facade, name):
        cache_variable = self._init_instance_cache(facade)
        return getattr(self, cache_variable).get(name, None)

    def _set_cache_instance(self, facade, name, instance):
        cache_variable = self._init_instance_cache(facade)
        getattr(self, cache_variable)[name] = instance

    def check_available(self, facade, key, warn=False):
        instance = self.get_instance(facade, key, required=False)
        if instance:
            if warn:
                self.warning(f"{facade.name.title()} {key} already exists")
            return False
        return True

    def check_exists(self, facade, key, warn=False):
        instance = self.get_instance(facade, key, required=False)
        if not instance:
            if warn:
                self.warning(f"{facade.name.title()} {key} does not exist")
            return False
        return True

    def get_instance_by_id(self, facade, id, required=True):
        instance = facade.retrieve_by_id(id)

        if not instance and required:
            self.error(f"{facade.name.title()} {id} does not exist")
        elif instance and instance.initialize(self):
            return instance
        return None

    def get_instance(self, facade, key, required=True, cache=True):
        instance = self._get_cache_instance(facade, key)

        if not cache or not instance:
            instance = facade.retrieve(key)

            if not instance and required:
                self.error(f"{facade.name.title()} {key} does not exist")
            else:
                if instance and instance.initialize(self):
                    self._set_cache_instance(facade, key, instance)
                else:
                    return None

        return instance

    def get_instances(self, facade, names=[], objects=[], groups=[], fields={}, cache=True):
        search_items = []
        results = {}

        if not names and not groups and not objects and not fields:
            search_items = facade.all()
        else:
            search_items.extend(data.ensure_list(names))
            search_items.extend(data.ensure_list(objects))

            for group in data.ensure_list(groups):
                search_items.extend(facade.keys(groups__name=group))

        def init_instance(object):
            if isinstance(object, str):
                cached = self._get_cache_instance(facade, object)
                if not cache or not cached:
                    instance = facade.retrieve(object)
                else:
                    instance = cached
            else:
                instance = object
                cached = self._get_cache_instance(facade, getattr(instance, facade.pk))

            if instance:
                id = getattr(instance, facade.pk)
                if not cache or not cached:
                    if instance.initialize(self):
                        self._set_cache_instance(facade, id, instance)
                    else:
                        instance = None
                else:
                    instance = cached

                if instance:
                    if fields:
                        for field, values in fields.items():
                            values = data.normalize_value(values)
                            value = getattr(instance, field, None)
                            if isinstance(values, str) and not value and re.match(r"^(none|null)$", values, re.IGNORECASE):
                                results[id] = instance
                            elif value and value in data.ensure_list(values):
                                results[id] = instance
                    else:
                        results[id] = instance
            else:
                self.error(f"{facade.name.title()} instance {object} does not exist")

        self.run_list(search_items, init_instance)
        return results.values()

    def search_instances(self, facade, queries=None, joiner="AND", error_on_empty=True, cache=True):
        if not queries:
            queries = []

        valid_fields = facade.query_fields
        queries = data.ensure_list(queries)
        joiner = joiner.upper()
        results = {}

        def perform_query(filters, excludes, fields):
            instances = facade.filter(**filters).exclude(**excludes)
            if len(instances) > 0:
                for instance in self.get_instances(facade, objects=list(instances), fields=fields, cache=cache):
                    results[getattr(instance, facade.pk)] = instance

        if queries:
            filters = {}
            excludes = {}
            extra = {}

            for query in queries:
                matches = re.search(r"^([\~\-])?([^\s\=]+)\s*(?:(\=|[^\s]*))\s*(.*)", query)

                if matches:
                    negate = True if matches.group(1) else False
                    field = matches.group(2).strip()
                    field_list = re.split(r"\.|__", field)

                    lookup = matches.group(3)
                    if not lookup and len(field_list) > 1:
                        lookup = field_list.pop()

                    value = re.sub(r"^[\'\"]|[\'\"]$", "", matches.group(4).strip())

                    if not lookup and not value:
                        value = field
                        lookup = "="
                        field_list[0] = facade.key()

                    base_field = field_list[0]
                    field_path = "__".join(field_list)
                    if lookup != "=":
                        field_path = f"{field_path}__{lookup}"

                    value = data.normalize_value(value, strip_quotes=False, parse_json=True)

                    if joiner.upper() == "OR":
                        filters = {}
                        excludes = {}
                        extra = {}

                    if base_field in valid_fields:
                        if negate:
                            excludes[field_path] = value
                        else:
                            filters[field_path] = value
                    else:
                        extra[field_path] = value

                    if joiner == "OR":
                        perform_query(filters, excludes, extra)
                else:
                    self.error("Search filter must be of the format: field[.subfield][.lookup] [=] value")

            if joiner == "AND":
                perform_query(filters, excludes, extra)
        else:
            for instance in self.get_instances(facade, cache=cache):
                results[getattr(instance, facade.pk)] = instance

        if error_on_empty and not results:
            if queries:
                self.warning("No {} instances were found: {}".format(facade.name, ", ".join(queries)))
            else:
                self.warning(f"No {facade.name} instances were found")

        return results.values()

    def save_instance(self, facade, key, fields=None, relation_key=False, quiet=False, normalize=True):
        if fields is None:
            fields = {}

        if normalize:
            fields = data.normalize_value(fields)

        instance = None
        provider_type = fields.pop("provider_type", None)

        if getattr(facade, "provider_name", None) and self.check_exists(facade, key):
            instance = self.get_instance(facade, key)

            if provider_type:
                instance.provider_type = provider_type

            instance.initialize(self, facade=facade)
            instance.provider.update(fields, relation_key=relation_key, quiet=quiet, normalize=False)
        elif getattr(facade, "provider_name", None):
            provider = self.get_provider(facade.provider_name, provider_type, facade=facade)
            instance = provider.create(key, fields, relation_key=relation_key, quiet=quiet, normalize=False)
        else:
            instance, created = facade.store(key, fields, relation_key=relation_key, command=self, normalize=False)
            if not quiet:
                if key:
                    self.success(f"Successfully saved {facade.name}: {key}")
                else:
                    self.success(f"Successfully saved new {facade.name}")

        self.send(f"data:save:{facade.meta.data_name}", getattr(instance, facade.pk))
        return instance

    def remove_instance(self, facade, key, scope=None):
        if scope:
            facade.set_scope(scope)

        if self.check_exists(facade, key):
            instance = self.get_instance(facade, key)
            instance_id = getattr(instance, facade.pk)

            if getattr(facade, "provider_name", None):
                instance.provider.delete(self.force)
            else:
                facade.delete(key)
                self.success(f"Successfully removed {facade.name}: {key}")

            self.send(f"data:remove:{facade.meta.data_name}", instance_id)
