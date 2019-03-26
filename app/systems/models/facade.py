from collections import OrderedDict

from django.conf import settings
from django.db.models import fields
from django.db.models.manager import Manager
from django.db.models.fields.related import ForeignKey
from django.utils.timezone import now, localtime

from utility import runtime, query, data, display, terminal

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


class ModelFacade(terminal.TerminalMixin):

    thread_lock = settings.DB_LOCK


    def __init__(self, cls):
        self.model = cls
        self.name = self.meta.verbose_name.replace(' ', '_')
        self.plural = self.meta.verbose_name_plural.replace(' ', '_')

        self.pk = self.meta.pk.name
        self.required = []
        self.optional = []
        self.fields = []

        self._scope = {}
        self.order = None
        self.limit = None

        for field in self.field_instances:
            if field.name != self.pk and field.name != self.key():
                if (not field.null
                    and field.blank == False
                    and field.default == fields.NOT_PROVIDED):
                    self.required.append(field.name)
                else:
                    self.optional.append(field.name)

            if field.name not in self.fields:
                self.fields.append(field.name)

    @property
    def manager(self):
        return settings.MANAGER

    @property
    def meta(self):
        return self.model._meta

    @property
    def field_instances(self):
        return self.meta.fields

    @property
    def field_index(self):
        return { f.name: f for f in self.field_instances }


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

    def get_base_scope(self):
        # Override in subclass
        #
        # Three choices: (non fields)
        # 1. Empty dictionary equals no filters
        # 2. Dictionary items are extra filters
        # 3. False means ABORT access/update attempt
        #
        return {}

    @property
    def scope_fields(self):
        if getattr(self.meta, 'scope', None):
            return data.ensure_list(self.meta.scope)
        return []

    @property
    def scope_parents(self):
        fields = OrderedDict()
        for name in self.scope_fields:
            field = getattr(self.model, name)
            if isinstance(field, ForeignKey):
                for parent in field.related_model.facade.scope_parents:
                    fields[parent] = True
            fields[name] = True
        return list(fields.keys())

    def set_scope(self, filters):
        self._scope = filters

    def get_scope_filters(self, instance):
        filters = {}

        for name in self.scope_fields:
            scope = getattr(instance, name, None)
            if scope:
                filters[name] = scope.name
                for name, value in scope.facade.get_scope_filters(scope).items():
                    filters[name] = value
        return filters

    def _check_scope(self, filters):
        base_scope = self.get_base_scope()
        if base_scope is False:
            raise ScopeError("Scope missing from {} query".format(self.name))

        for filter, value in base_scope.items():
            if not filter in filters:
                filters[filter] = value

        for filter, value in self._scope.items():
            if not filter in filters:
                filters[filter] = value

    def get_children(self):
        children = []
        for model in self.manager.get_models():
            model_fields = self.field_index
            fields = list(model.facade.get_base_scope().keys())
            fields.extend(model.facade.scope_fields)

            for field in fields:
                field = model_fields[field.replace('_id', '')]

                if isinstance(field, ForeignKey):
                    if self.model == field.related_model:
                        children.append(model.facade.name)
                        break
        return children


    def get_relation(self):
        # Override in subclass
        return {}

    def get_relations(self):
        # Override in subclass
        return {}

    def get_all_relations(self):
        return {**self.get_relation(), **self.get_relations()}


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
                raise ScopeError("Scope missing from {} {} retrieval".format(self.name, key))

            return data


    def ensure(self, command):
        # Override in subclass
        pass

    def _keep(self):
        if settings.API_EXEC:
            return self.keep()
        return []

    def keep(self):
        # Override in subclass
        return []

    def _keep_relations(self):
        if settings.API_EXEC:
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
            if instance and (getattr(instance, 'type', None) is None or not instance.type.startswith('sys_')):
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

                    data.append((
                        self.header_color(label),
                        value
                    ))

            data.append((' ', ' '))
            for field, params in relations.items():
                label = self.header_color(relations[field][1].title())
                value = getattr(instance, field)

                if isinstance(value, Manager):
                    instances = { x.id: x for x in value.all() }
                    relation_data = self.render_relation_overview(command, relations[field][0], instances)
                    if relation_data:
                        value = display.format_data(relation_data)
                        data.append((label, value + "\n"))
                else:
                    data.append((label, self.relation_color(str(value)) + "\n"))
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
        data[0] = [ self.header_color(x) for x in labels ]
        if len(data) > 1:
            for index, info in enumerate(data[1:]):
                id = info.pop(0)
                for field, params in relations.items():
                    items = []
                    value = getattr(instances[id], field)

                    if isinstance(value, Manager):
                        for sub_instance in value.all():
                            items.append(self.relation_color(str(sub_instance)))
                    else:
                        items.append(self.relation_color(str(value)))

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
            id_index = data[0].index(self.pk)
            key_index = (data[0].index(self.key()) - 1)

            for index, info in enumerate(data):
                id = info.pop(id_index)

                if index == 0:
                    if relations:
                        info.extend([ self.header_color(relations[x][1].title()) for x in relations.keys() ])

                    if processor and callable(processor):
                        processor('label', info, key_index)
                else:
                    instance = command.get_instance_by_id(self, id, required = False)

                    info[key_index] = info[key_index]

                    for field, params in relations.items():
                        items = []
                        value = getattr(instance, field)

                        if isinstance(value, Manager):
                            for sub_instance in value.all():
                                items.append(self.relation_color(str(sub_instance)))
                        else:
                            items.append(self.relation_color(str(value)))

                        info.append("\n".join(items))

                    if processor and callable(processor):
                        processor('data', info, key_index)

        if len(data):
            for index, value in enumerate(data[0]):
                try:
                    existing_index = fields.index(value)
                    data[0][index] = self.header_color(labels[existing_index])
                except Exception as e:
                    pass

        return data
