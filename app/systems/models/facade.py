from django.conf import settings
from django.db.models import fields
from django.db.models.manager import Manager
from django.utils.timezone import now, localtime

from utility import runtime, query, data, display

import datetime
import binascii
import os
import re
import hashlib

import warnings


warnings.filterwarnings(u'ignore',
    message = r'DateTimeField [^\s]+ received a naive datetime',
    category = RuntimeWarning,
)


class ScopeError(Exception):
    pass

class AccessError(Exception):
    pass

class RestrictedError(Exception):
    pass


class ModelFacade:

    thread_lock = settings.DB_LOCK


    def __init__(self, cls):
        self.model = cls
        self.name = cls.__name__.lower()

        self.pk = self.model._meta.pk.name
        self.required = []
        self.optional = []
        self.fields = [self.pk]
        post_fields = []

        if self.pk != self.key():
            self.fields.append(self.key())

        self._scope = {}
        self.order = None
        self.limit = None

        scope = self.scope(True)
        if scope:
            for field in scope:
                self.fields.append(field)

        for field in self.model._meta.fields:
            if field.name != self.pk and field.name != self.key():
                self.optional.append(field.name)

                if (not field.null
                    and field.blank == False
                    and field.default == fields.NOT_PROVIDED):
                    self.required.append(field.name)

            if field.name in ['created', 'updated']:
                post_fields.append(field.name)
            elif field.name not in self.fields:
                self.fields.append(field.name)

        for field in post_fields:
            self.fields.append(field)


    def get_packages(self):
        return ['all']


    def hash(self, *args):
        return hashlib.sha256("-".join(sorted(args)).encode()).hexdigest()

    def tokenize(self, seed):
        return binascii.hexlify(seed).decode()

    def generate_token(self, size = 40):
        return self.tokenize(os.urandom(size))[:size]


    def key(self):
        # Override in subclass if model is scoped
        return self.pk

    def scope(self, fields = False):
        # Override in subclass
        #
        # Three choices: (non fields)
        # 1. Empty dictionary equals no filters
        # 2. Dictionary items are extra filters
        # 3. False means ABORT access/update attempt
        #
        if fields:
            return []
        return {}

    def get_scopes(self):
        # Override in subclass
        return []

    def parse_scopes(self, command):
        for name in self.get_scopes():
            getattr(command, "parse_{}_name".format(name))("--{}".format(name))

    def set_scopes(self, command, optional = False):
        filters = {}
        for name in self.get_scopes():
            if optional and not getattr(command, "{}_name".format(name), None):
                name = None

            if name:
                instance = getattr(command, name)
                command.options.add("{}_name".format(name), instance.name)
                if name in self.fields:
                    filters["{}_id".format(name)] = instance.id

        self._scope = filters

    def get_scope_options(self, instance):
        options = {}
        for name in self.get_scopes():
            scope = getattr(instance, name, None)
            if scope:
                options["{}_name".format(name)] = scope.name
                for name_field, name_value in scope.facade.get_scope_options(scope).items():
                    options[name_field] = name_value

        return options

    def _check_scope(self, filters):
        scope = self.scope()

        if scope is False:
            raise ScopeError("Scope missing from {} query".format(self.model.__name__))

        for filter, value in scope.items():
            if not filter in filters:
                filters[filter] = value

        for filter, value in self._scope.items():
            if not filter in filters:
                filters[filter] = value


    def get_relation(self):
        # Override in subclass
        return {}

    def get_relations(self):
        # Override in subclass
        return {}

    def get_all_relations(self):
        return {**self.get_relation(), **self.get_relations()}

    def parse_relations(self, command):
        for field_name, info in self.get_relation().items():
            if len(info) > 2:
                getattr(command, "parse_{}_name".format(info[0]))(*info[2:])

        for field_name, info in self.get_relations().items():
            if len(info) > 2:
                getattr(command, "parse_{}_names".format(info[0]))(*info[2:])

    def get_relation_names(self, command):
        relations = {}
        for name, info in self.get_relation().items():
            field = "{}_name".format(info[0])
            relations[name] = getattr(command, field, None)

        for name, info in self.get_relations().items():
            field = "{}_names".format(info[0])
            relations[name] = getattr(command, field, None)

        return relations

    def get_children(self):
        # Override in subclass
        return []


    def default_order(self):
        return 'created'

    def set_order(self, order):
        self.order = [
            re.sub(r'^~', '-', x) for x in data.ensure_list(order)
        ]

    def set_limit(self, limit):
        self.limit = limit


    def query(self, **filters):
        with self.thread_lock:
            self._check_scope(filters)

            manager = self.model.objects
            if not filters:
                queryset = manager.all().distinct()
            else:
                queryset = manager.filter(**filters).distinct()

            if self.order:
                queryset = queryset.order_by(*self.order)
            elif self.default_order():
                queryset = queryset.order_by(*data.ensure_list(self.default_order()))

            if self.limit:
                queryset = queryset[:self.limit]

            return queryset

    def all(self):
        return self.query()

    def filter(self, **filters):
        return self.query(**filters)


    def keys(self, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.values_list(self.key(), flat = True)

    def field_values(self, name, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.values_list(name, flat = True)

    def values(self, *fields, **filters):
        if not fields:
            fields = self.fields

        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.values(*fields)

    def count(self, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.count()

    def related(self, key, relation, **filters):
        instance = self.retrieve(key)
        queryset = None

        if instance:
            with self.thread_lock:
                queryset = query.get_queryset(instance, relation)

                if queryset:
                    if filters:
                        queryset = queryset.filter(**filters).distinct()
                    else:
                        queryset = queryset.all()

        return queryset


    def retrieve_by_id(self, id):
        with self.thread_lock:
            filters = {}
            self._check_scope(filters)

            try:
                filters[self.pk] = id
                data = self.model.objects.get(**filters)

            except self.model.DoesNotExist:
                return None

            return data

    def retrieve(self, key, **filters):
        with self.thread_lock:
            self._check_scope(filters)

            try:
                filters[self.key()] = key
                data = self.model.objects.get(**filters)

            except self.model.DoesNotExist:
                return None

            except self.model.MultipleObjectsReturned:
                raise ScopeError("Scope missing from {} {} retrieval".format(self.model.__name__, key))

            return data


    def ensure(self, command):
        # Override in subclass
        pass

    def _keep(self):
        if runtime.Runtime.api():
            return self.keep()
        return []

    def keep(self):
        # Override in subclass
        return []

    def _keep_relations(self):
        if runtime.Runtime.api():
            return self.keep_relations()
        return {}

    def keep_relations(self):
        # Override in subclass
        return {}


    def create(self, key, **values):
        values[self.key()] = key
        self._check_scope(values)
        return self.model(**values)

    def store(self, key, **values):
        filters = { self.key(): key }
        self._check_scope(filters)

        instance, created = self.model.objects.get_or_create(**filters)
        values = data.normalize_dict(values)

        for field, value in values.items():
            setattr(instance, field, value)

        instance.save()
        return (instance, created)

    def delete(self, key, **filters):
        if key not in data.ensure_list(self._keep()):
            filters[self.key()] = key
            return self.clear(**filters)
        else:
            raise RestrictedError("Removal of {} {} is restricted".format(self.model.__name__.lower(), key))

    def clear(self, **filters):
        queryset = self.query(**filters)

        with self.thread_lock:
            if self._keep():
                queryset = queryset.exclude(**{
                    "{}__in".format(self.key()): data.ensure_list(self._keep())
                })
            deleted, del_per_type = queryset.delete()

            if deleted:
                return True
            return False


    def get_list_fields(self):
        # Override in subclass
        return self.fields

    def get_display_fields(self):
        # Override in subclass
        return self.fields

    def get_field_created_display(self, instance, value, short):
        return localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")

    def get_field_updated_display(self, instance, value, short):
        return localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")


    def render(self, command, fields, queryset):
        fields = list(fields)
        data = [fields]

        for instance in queryset:
            instance = command.get_instance_by_id(self, instance.id, required = False)
            if instance:
                record = []

                for field in fields:
                    display_method = getattr(self, "get_field_{}_display".format(field), None)
                    value = getattr(instance, field, None)

                    if display_method and callable(display_method):
                        value = display_method(instance, value, True)

                    elif isinstance(value, datetime.datetime):
                        value = localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")

                    record.append(value)

                data.append(record)

        return data


    def render_display(self, command, key):
        from .base import AppModel

        if isinstance(key, AppModel):
            instance = key
        else:
            instance = command.get_instance(self, key, required = False)

        relations = self.get_all_relations()
        data = []

        if instance:
            for field in self.get_display_fields():
                if isinstance(field, str) and field[0] == '-':
                    data.append((' ', ' '))
                else:
                    if isinstance(field, (list, tuple)):
                        label = field[1]
                        field = field[0]
                    else:
                        label = field.title()

                    display_method = getattr(self, "get_field_{}_display".format(field), None)
                    value = getattr(instance, field, None)

                    if display_method and callable(display_method):
                        value = display_method(instance, value, False)
                    else:
                        if isinstance(value, datetime.datetime):
                            value = localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")
                        else:
                            value = str(value)

                    data.append((label, value))

            data.append(('', ''))
            for field, params in relations.items():
                label = relations[field][1].title()
                value = getattr(instance, field)

                if isinstance(value, Manager):
                    instances = { x.id: x for x in value.all() }
                    relation_data = self.render_relation_overview(command, relations[field][0], instances)
                    if relation_data:
                        value = display.format_data(relation_data)
                        data.append((label, value + "\n"))
                else:
                    data.append((label, str(value) + "\n"))
        else:
            raise AccessError("{} {} does not exist".format(self.name.title(), key))

        return data

    def render_list_fields(self):
        fields = []
        labels = []

        for field in self.get_list_fields():
            if isinstance(field, (list, tuple)):
                fields.append(field[0])
                labels.append(field[1])
            else:
                fields.append(field)
                labels.append(field)

        return (fields, labels)


    def render_relation_overview(self, command, name, instances):
        facade = getattr(command, "_{}".format(name))
        relations = facade.get_all_relations()
        fields, labels = facade.render_list_fields()
        labels.extend([ relations[x][1].title() for x in relations.keys() ])

        data = facade.render(command, ['id'] + fields,
            facade.filter(**{
                'id__in': instances.keys()
            })
        )
        data[0] = labels
        if len(data) > 1:
            for index, info in enumerate(data[1:]):
                id = info.pop(0)
                for field, params in relations.items():
                    items = []
                    value = getattr(instances[id], field)

                    if isinstance(value, Manager):
                        for sub_instance in value.all():
                            items.append(str(sub_instance))
                    else:
                        items.append(str(value))

                    info.append("\n".join(items))
        else:
            data = []
        return data

    def render_list(self, command, processor = None, filters = {}):
        relations = self.get_all_relations()
        data = []
        fields, labels = self.render_list_fields()

        if self.count(**filters):
            data = self.render(command, ['id'] + fields, self.filter(**filters))
            key_index = data[0].index(self.key())

            for index, info in enumerate(data):
                id = info.pop(0)

                if index == 0:
                    if relations:
                        info.extend([ relations[x][1].title() for x in relations.keys() ])

                    if processor and callable(processor):
                        processor('label', info, key_index)
                else:
                    instance = command.get_instance_by_id(self, id, required = False)

                    for field, params in relations.items():
                        items = []
                        value = getattr(instance, field)

                        if isinstance(value, Manager):
                            for sub_instance in value.all():
                                items.append(str(sub_instance))
                        else:
                            items.append(str(value))

                        info.append("\n".join(items))

                    if processor and callable(processor):
                        processor('data', info, key_index)

        if len(data):
            for index, value in enumerate(data[0]):
                try:
                    existing_index = fields.index(value)
                    data[0][index] = labels[existing_index]
                except Exception as e:
                    pass

        return data
