from systems.command import args
from utility import text, data
from .meta import MetaDataMixin

import re
import copy
import json


class DataMixin(object, metaclass = MetaDataMixin):

    def parse_flag(self, name, flag, help_text):
        if name not in self.option_map:
            self.add_schema_field(name,
                args.parse_bool(self.parser, name, flag, help_text),
                True
            )
            self.option_map[name] = True

    def parse_variable(self, name, optional, type, help_text, value_label = None, default = None, choices = None):
        if name not in self.option_map:
            if optional and isinstance(optional, (str, list, tuple)):
                if not value_label:
                    value_label = name

                self.add_schema_field(name,
                    args.parse_option(self.parser, name, optional, type, help_text,
                        value_label = value_label.upper(),
                        default = default,
                        choices = choices
                    ),
                    True
                )
            else:
                self.add_schema_field(name,
                    args.parse_var(self.parser, name, type, help_text,
                        optional = optional,
                        default = default,
                        choices = choices
                    ),
                    optional
                )
            self.option_map[name] = True

    def parse_variables(self, name, optional, type, help_text, value_label = None, default = None):
        if name not in self.option_map:
            if optional and isinstance(optional, (str, list, tuple)):
                help_text = "{} (comma separated)".format(help_text)

                if not value_label:
                    value_label = name

                self.add_schema_field(name,
                    args.parse_csv_option(self.parser, name, optional, help_text,
                        value_label = value_label.upper(),
                        default = default
                    ),
                    True
                )
            else:
                self.add_schema_field(name,
                    args.parse_vars(self.parser, name, type, help_text,
                        optional = optional
                    ),
                    optional
                )
            self.option_map[name] = True

    def parse_fields(self, facade, name, optional = False, excluded_fields = [], help_callback = None, callback_args = [], callback_options = {}):
        if name not in self.option_map:
            if facade:
                required_text = [self.warning_color(x) for x in facade.required if x not in list(excluded_fields)]
                optional_text = [self.key_color(x) for x in facade.optional if x not in excluded_fields]
                help_text = "\n".join(text.wrap("fields as key value pairs\n\nrequirements: {}\n\noptions: {}".format(", ".join(required_text), ", ".join(optional_text)), 60))
            else:
                help_text = "\nfields as key value pairs\n"

            if help_callback and callable(help_callback):
                help_text += "\n".join(help_callback(*callback_args, **callback_options))

            self.add_schema_field(name,
                args.parse_key_values(self.parser, name, help_text,
                    value_label = 'field=VALUE',
                    optional = optional
                ),
                optional
            )
            self.option_map[name] = True


    def parse_test(self):
        self.parse_flag('test', '--test', 'test execution without permanent changes')

    @property
    def test(self):
        return self.options.get('test', False)


    def parse_plan(self):
        self.parse_flag('plan', '--plan', 'generate plan of potential changes')

    @property
    def plan(self):
        return self.options.get('plan', False)


    def parse_force(self):
        self.parse_flag('force', '--force', 'force execution even with provider errors')

    @property
    def force(self):
        return self.options.get('force', False)


    def parse_count(self):
        self.parse_variable('count',
            '--count', int,
            'instance count (default 1)',
            value_label = 'COUNT',
            default = 1
        )

    @property
    def count(self):
        return self.options.get('count', 1)


    def parse_clear(self):
        self.parse_flag('clear', '--clear', 'clear all items')

    @property
    def clear(self):
        return self.options.get('clear', False)


    def parse_scope(self, facade):
        for name in facade.scope_parents:
            getattr(self, "parse_{}_name".format(name))("--{}".format(name))

    def set_scope(self, facade, optional = False):
        filters = {}
        for name in facade.scope_parents:
            instance_name = getattr(self, "{}_name".format(name), None)
            if optional and not instance_name:
                name = None

            if name:
                sub_facade = getattr(self, "_{}".format(name))
                self.set_scope(sub_facade)

                instance = self.get_instance(sub_facade, instance_name)
                if name in facade.fields:
                    filters["{}_id".format(name)] = instance.id

        facade.set_scope(filters)

    def get_scope_filters(self, instance):
        facade = instance.facade
        filters = {}
        for name, value in facade.get_scope_filters(instance).items():
            filters["{}_name".format(name)] = value
        return filters


    def parse_relations(self, facade):
        for field_name, info in facade.get_relations().items():
            name = info['name']
            if name != 'environment':
                option_name = "--{}".format(field_name)

                if info['multiple']:
                    method_name = "parse_{}_names".format(name)
                else:
                    method_name = "parse_{}_name".format(name)

                getattr(self, method_name)(option_name)

    def get_relations(self, facade):
        relations = {}
        for field_name, info in facade.get_relations().items():
            name = info['name']
            sub_facade = getattr(self, "_{}".format(name), None)
            if sub_facade:
                self.set_scope(sub_facade)

            if info['multiple']:
                method_name = "{}_names".format(name)
            else:
                method_name = "{}_name".format(name)

            relations[field_name] = getattr(self, method_name, None)

        return relations


    def check_available(self, facade, name, warn = False):
        instance = self.get_instance(facade, name, required = False)
        if instance:
            if warn:
                self.warning("{} {} already exists".format(
                    facade.name.title(),
                    name
                ))
            return False
        return True

    def check_exists(self, facade, name, warn = False):
        instance = self.get_instance(facade, name, required = False)
        if not instance:
            if warn:
                self.warning("{} {} does not exist".format(
                    facade.name.title(),
                    name
                ))
            return False
        return True


    def get_instance_by_id(self, facade, id, required = True):
        instance = facade.retrieve_by_id(id)

        if not instance and required:
            self.error("{} {} does not exist".format(facade.name.title(), id))
        elif instance and instance.initialize(self):
            return instance
        return None

    def get_instance(self, facade, name, required = True):
        instance = self._get_cache_instance(facade, name)

        if not instance:
            instance = facade.retrieve(name)

            if not instance and required:
                self.error("{} {} does not exist".format(facade.name.title(), name))
            else:
                if instance and instance.initialize(self):
                    self._set_cache_instance(facade, name, instance)
                else:
                    return None

        return instance


    def get_instances(self, facade,
        names = [],
        objects = [],
        groups = [],
        fields = {}
    ):
        search_items = []
        results = {}

        if not names and not groups and not objects and not fields:
            search_items = facade.all()
        else:
            search_items.extend(data.ensure_list(names))
            search_items.extend(data.ensure_list(objects))

            for group in data.ensure_list(groups):
                search_items.extend(facade.keys(groups__name = group))

        def init_instance(object):
            if isinstance(object, str):
                cached = self._get_cache_instance(facade, object)
                if not cached:
                    instance = facade.retrieve(object)
            else:
                instance = object
                cached = self._get_cache_instance(facade, getattr(instance, facade.pk))

            if instance:
                id = getattr(instance, facade.pk)
                if not cached:
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
                            if isinstance(values, str) and not value and re.match(r'^(none|null)$', values, re.IGNORECASE):
                                results[id] = instance
                            elif value and value in data.ensure_list(values):
                                results[id] = instance
                    else:
                        results[id] = instance
            else:
                self.error("{} instance {} does not exist".format(facade.name.title(), data))

        self.run_list(search_items, init_instance)
        return results.values()


    def search_instances(self, facade, queries = [], joiner = 'AND', error_on_empty = True):
        valid_fields = facade.query_fields
        queries = data.ensure_list(queries)
        joiner = joiner.upper()
        results = {}

        def perform_query(filters, fields):
            instances = facade.query(**filters)
            if len(instances) > 0:
                for instance in self.get_instances(facade,
                    objects = list(instances),
                    fields = fields
                ):
                    results[getattr(instance, facade.pk)] = instance

        if queries:
            filters = {}
            extra = {}

            for query in queries:
                matches = re.search(r'^([^\=]+)\s*\=\s*(.+)', query)

                if matches:
                    field = matches.group(1)
                    value = matches.group(2)

                    if ',' in value:
                        value = [ x.trim() for x in value.split(',') ]

                    if joiner == 'OR':
                        filters = {}
                        extra = {}

                    if field.split('__')[0] in valid_fields:
                        filters[field] = value
                    else:
                        extra[field] = value

                    if joiner == 'OR':
                        perform_query(filters, extra)
                else:
                    self.error("Search filter must be of the format: field[__check]=value".format(query))

            if joiner == 'AND':
                perform_query(filters, extra)
        else:
            results.extend(self.get_instances(facade))

        if error_on_empty and not results:
            if queries:
                self.warning("No {} instances were found: {}".format(facade.name, ", ".join(queries)))
            else:
                self.warning("No {} instances were found".format(facade.name))

        return results.values()


    def facade(self, facade):
        if getattr(self, '_facade_cache', None) is None:
            self._facade_cache = {}

        if not isinstance(facade, str):
            name = facade.name
        else:
            name = facade
            facade = self.manager.get_facade_index()[name]

        if not self._facade_cache.get(name, None):
            self._facade_cache[name] = copy.deepcopy(facade)

        return self._facade_cache[name]


    def _init_instance_cache(self, facade):
        cache_variable = "_data_{}_cache".format(facade.name)

        if not getattr(self, cache_variable, None):
            setattr(self, cache_variable, {})

        return cache_variable

    def _get_cache_instance(self, facade, name):
        cache_variable = self._init_instance_cache(facade)
        return getattr(self, cache_variable).get(name, None)

    def _set_cache_instance(self, facade, name, instance):
        cache_variable = self._init_instance_cache(facade)
        getattr(self, cache_variable)[name] = instance
