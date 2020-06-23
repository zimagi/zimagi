from collections import OrderedDict

from systems.commands import args
from utility import text, data
from .meta import MetaBaseMixin

import re
import copy
import json


class BaseMixin(object, metaclass = MetaBaseMixin):

    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass


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

    def parse_fields(self, facade, name, optional = False, help_callback = None, callback_args = None, callback_options = None, exclude_fields = None):
        if not callback_args:
            callback_args = []
        if not callback_options:
            callback_options = {}

        if exclude_fields:
            exclude_fields = data.ensure_list(exclude_fields)
            callback_options['exclude_fields'] = exclude_fields

        if name not in self.option_map:
            if facade:
                help_text = "\n".join(self.field_help(facade, exclude_fields))
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


    def parse_search(self, optional = True, help_text = 'one or more search queries'):
        self.parse_variables('instance_search_query', optional, str, help_text,
            value_label = 'REFERENCE'
        )
        self.parse_flag('instance_search_or', '--or', 'perform an OR query on input filters')

    @property
    def search_queries(self):
        return self.options.get('instance_search_query', [])

    @property
    def search_join(self):
        join_or = self.options.get('instance_search_or', False)
        return 'OR' if join_or else 'AND'


    def parse_scope(self, facade):
        for name in facade.scope_parents:
            getattr(self, "parse_{}_name".format(name))("--{}".format(name.replace('_', '-')))

    def parse_dependency(self, facade):
        for name in facade.relation_fields:
            getattr(self, "parse_{}_name".format(name))("--{}".format(name.replace('_', '-')))

    def set_scope(self, facade, optional = False):
        relations = facade.relation_fields
        filters = {}
        for name in OrderedDict.fromkeys(facade.scope_parents + relations).keys():
            instance_name = getattr(self, "{}_name".format(name), None)
            if (optional or name in relations) and not instance_name:
                name = None

            if name and name in facade.fields:
                sub_facade = getattr(self, "_{}".format(
                    facade.get_subfacade(name).name
                ))
                if facade.name != sub_facade.name:
                    self.set_scope(sub_facade, optional)
                else:
                    sub_facade.set_scope(filters)

                if instance_name:
                    instance = self.get_instance(sub_facade, instance_name, required = not optional)
                    if instance:
                        filters["{}_id".format(name)] = instance.id
                    elif not optional:
                        self.error("{} {} does not exist".format(facade.name.title(), instance_name))

        facade.set_scope(filters)
        return filters

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
                option_name = "--{}".format(field_name.replace('_', '-'))

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
                self.set_scope(sub_facade, True)

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
                    instance = cached
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
                self.error("{} instance {} does not exist".format(facade.name.title(), object))

        self.run_list(search_items, init_instance)
        return results.values()


    def search_instances(self, facade, queries = None, joiner = 'AND', error_on_empty = True):
        if not queries:
            queries = []

        valid_fields = facade.query_fields
        queries = data.ensure_list(queries)
        joiner = joiner.upper()
        results = {}

        def perform_query(filters, excludes, fields):
            instances = facade.query(**filters).exclude(**excludes)
            if len(instances) > 0:
                for instance in self.get_instances(facade,
                    objects = list(instances),
                    fields = fields
                ):
                    results[getattr(instance, facade.pk)] = instance

        if queries:
            filters = {}
            excludes = {}
            extra = {}

            for query in queries:
                matches = re.search(r'^(\~)?([^\s\=]+)\s*(?:(\=|[^\s]*))\s*(.*)', query)

                if matches:
                    negate = True if matches.group(1) else False
                    field = matches.group(2).strip()
                    field_list = field.split('.')

                    lookup = matches.group(3)
                    if not lookup:
                        lookup = field_list.pop()

                    value = matches.group(4)

                    base_field = field_list[0]
                    field_path = "__".join(field_list)
                    if lookup != '=':
                        field_path = "{}__{}".format(field_path, lookup)

                    if ',' in value:
                        value = [ x.strip() for x in value.split(',') ]

                    if value in ('null', 'NULL', 'none', 'None'):
                        value = None
                    elif value in ('true', 'True', 'TRUE') or lookup == 'isnull' and value == '':
                        value = True
                    elif value in ('false', 'False', 'FALSE'):
                        value = False

                    if joiner.upper() == 'OR':
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

                    if joiner == 'OR':
                        perform_query(filters, excludes, extra)
                else:
                    self.error("Search filter must be of the format: field[.subfield][.lookup] [=] value".format(query))

            if joiner == 'AND':
                perform_query(filters, excludes, extra)
        else:
            for instance in self.get_instances(facade):
                results[getattr(instance, facade.pk)] = instance

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
            facade = self.manager.index.get_facade_index()[name]

        if not self._facade_cache.get(name, None):
            self._facade_cache[name] = copy.deepcopy(facade)

        return self._facade_cache[name]


    def field_help(self, facade, exclude_fields = None):
        field_index = facade.field_index
        system_fields = [ x.name for x in facade.system_field_instances ]

        if facade.name == 'user':
            system_fields.extend(['last_login', 'password']) # User abstract model exceptions

        lines = [ "fields as key value pairs", '' ]

        lines.append('requirements:')
        for name in facade.required:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace('Field', '').lower()
                if field_label == 'char':
                    field_label = 'string'

                choices = []
                if field.choices:
                    choices = [ self.value_color(x[0]) for x in field.choices ]

                lines.append("    {} {}{}".format(
                    self.warning_color(field.name),
                    field_label,
                    ':> ' + ", ".join(choices) if choices else ''
                ))
                if field.help_text:
                    lines.extend(('',
                        "       - {}".format(
                            "\n".join(text.wrap(field.help_text, 40,
                                indent = "         "
                            ))
                        ),
                    ))
        lines.append('')

        lines.append('options:')
        for name in facade.optional:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace('Field', '').lower()
                if field_label == 'char':
                    field_label = 'string'

                choices = []
                if field.choices:
                    choices = [ self.value_color(x[0]) for x in field.choices ]

                lines.append("    {} {} ({}){}".format(
                    self.key_color(field.name),
                    field_label,
                    self.value_color(str(facade.get_field_default(field))),
                    ':> ' + ", ".join(choices) if choices else ''
                ))
                if field.help_text:
                    lines.extend(('',
                        "       - {}".format(
                            "\n".join(text.wrap(field.help_text, 40,
                                indent = "         "
                            ))
                        ),
                    ))
        lines.append('')
        return lines


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
