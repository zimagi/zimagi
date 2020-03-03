from collections import OrderedDict
from functools import lru_cache

from django.conf import settings
from django.db.models import fields
from django.db.models.manager import Manager
from django.db.models.fields import NOT_PROVIDED, Field
from django.db.models.fields.related import RelatedField, ForeignKey, ManyToManyField
from django.db.models.fields.reverse_related import ForeignObjectRel, ManyToOneRel, OneToOneRel, ManyToManyRel
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.utils.timezone import now, localtime

from utility import runtime, query, data, display, terminal

import datetime
import binascii
import os
import re
import hashlib
import warnings


class ScopeError(Exception):
    pass

class AccessError(Exception):
    pass

class RestrictedError(Exception):
    pass


class ModelFacade(terminal.TerminalMixin):

    thread_lock = settings.DB_LOCK


    def __init__(self, cls):
        super().__init__()

        self.model = cls
        self.name = self.meta.verbose_name.replace(' ', '_')
        self.plural = self.meta.verbose_name_plural.replace(' ', '_')

        self.pk = self.meta.pk.name
        self.required = []
        self.optional = []
        self.fields = []
        self.field_map = {}

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
                self.field_map[field.name] = field

    @property
    def manager(self):
        return settings.MANAGER


    def get_subfacade(self, field_name):
        field = self.field_map[field_name]
        return field.related_model.facade


    @property
    def meta(self):
        return self.model._meta

    @property
    @lru_cache(maxsize = None)
    def field_instances(self):
        fields = list(self.meta.fields)
        for field in self.dynamic_fields:
            fields.append(Field(
                name = field,
                verbose_name = field.replace('_', ' '),
                editable = False
            ))
        return fields

    @property
    def system_field_instances(self):
        fields = []
        for field in self.field_instances:
            if not field.editable:
                fields.append(field)
        return fields

    @property
    def dynamic_fields(self):
        if getattr(self.meta, 'dynamic_fields', None):
            return data.ensure_list(self.meta.dynamic_fields)
        return []

    @property
    def query_fields(self):
        fields = set(list(self.fields) + list(self.get_all_relations().keys()))
        return [ x for x in fields if x not in self.dynamic_fields ]

    @property
    def field_index(self):
        return { f.name: f for f in self.meta.get_fields() }


    def check_field_related(self, field):
        return isinstance(field, (RelatedField, ForeignObjectRel))

    def get_field_default(self, field):
        if field.default == NOT_PROVIDED:
            return None
        return field.default


    def get_packages(self):
        packages = [
            settings.DB_PACKAGE_ALL_NAME,
            self.name
        ]
        packages.extend(self.get_children(True))
        return list(set(packages))


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
    @lru_cache(maxsize = None)
    def scope_fields(self):
        if getattr(self.meta, 'scope', None):
            return data.ensure_list(self.meta.scope)
        return []

    @property
    @lru_cache(maxsize = None)
    def relation_fields(self):
        scope = []
        if getattr(self.meta, 'relation', None):
            for field in data.ensure_list(self.meta.relation):
                if field not in self.scope_fields:
                    scope.append(field)
        return scope

    @property
    @lru_cache(maxsize = None)
    def scope_parents(self):
        fields = OrderedDict()
        for name in self.scope_fields:
            field = getattr(self.model, name)
            if isinstance(field, ForwardManyToOneDescriptor):
                for parent in field.field.related_model.facade.scope_parents:
                    fields[parent] = True
            fields[name] = True
        return list(fields.keys())

    def scope_name_filters(self, base_field = None):
        filters = {}
        for name in self.scope_fields:
            field = getattr(self.model, name)
            if isinstance(field, ForwardManyToOneDescriptor):
                for parent, field_filter in field.field.related_model.facade.scope_name_filters(name).items():
                    filters[parent] = field_filter
            if base_field:
                filters[name] = "{}__{}__name".format(base_field, name)
            else:
                filters[name] = "{}__name".format(name)
        return filters


    def set_scope(self, filters):
        self._scope = filters

    def get_scope(self):
        return self._scope

    def get_scope_name(self):
        return self.hash(*[ v for k,v in self.get_scope().items() ])

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

        for filter, value in self.get_scope().items():
            if not filter in filters:
                filters[filter] = value


    @lru_cache(maxsize = None)
    def get_children(self, recursive = False, process = 'all'):
        children = []
        for model in self.manager.get_models():
            model_fields = { f.name: f for f in model._meta.fields }
            fields = list(model.facade.get_base_scope().keys())
            fields.extend(model.facade.scope_fields)

            for field in fields:
                field = model_fields[field.replace('_id', '')]

                if isinstance(field, ForeignKey):
                    if self.model == field.related_model:
                        scope_process = model.facade.meta.scope_process

                        if process == 'all' or process == scope_process:
                            children.append(model.facade.name)
                            if recursive:
                                children.extend(model.facade.get_children(True, process))
                            break
        return children

    @lru_cache(maxsize = None)
    def get_relations(self):
        scope_fields = self.scope_fields
        relations = {}
        for field in self.meta.get_fields():
            if field.name not in scope_fields and isinstance(field, (ForeignKey, ManyToManyField)):
                model_meta = field.related_model._meta

                if isinstance(field, ManyToManyField):
                    name = model_meta.verbose_name.replace(' ', '_')
                    label = model_meta.verbose_name_plural
                    multiple = True
                elif isinstance(field, ForeignKey):
                    name = field.name
                    label = model_meta.verbose_name
                    multiple = False

                relations[field.name] = {
                    'name': name,
                    'label': label.title(),
                    'model': field.related_model,
                    'field': field,
                    'multiple': multiple
                }
        return relations

    @lru_cache(maxsize = None)
    def get_reverse_relations(self):
        relations = {}
        for field in self.meta.get_fields():
            if field.auto_created and not field.concrete:
                if self.model != field.related_model:
                    model_meta = field.related_model._meta
                    name = model_meta.verbose_name.replace(' ', '_')

                    if isinstance(field, (ManyToOneRel, ManyToManyRel)):
                        label = model_meta.verbose_name_plural
                        multiple = True
                    elif isinstance(field, OneToOneRel):
                        label = model_meta.verbose_name
                        multiple = False

                    if name not in ('log', 'state'):
                        relations[field.name] = {
                            'name': name,
                            'label': label.title(),
                            'model': field.related_model,
                            'field': field,
                            'multiple': multiple
                        }
        return relations

    @lru_cache(maxsize = None)
    def get_all_relations(self):
        scope_relations = {}
        for field in self.meta.get_fields():
            if field.name in self.scope_fields:
                model_meta = field.related_model._meta
                scope_relations[field.name] = {
                    'name': field.name,
                    'label': model_meta.verbose_name.title(),
                    'model': field.related_model,
                    'field': field,
                    'multiple': False
                }
        return {
            **scope_relations,
            **self.get_relations(),
            **self.get_reverse_relations()
        }


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
                queryset = manager.all()
            else:
                queryset = manager.filter(**filters)

            if self.order:
                queryset = queryset.order_by(*self.order)

            if self.limit:
                queryset = queryset[:self.limit]

            return queryset

    def all(self):
        return self.query()

    def filter(self, **filters):
        return self.query(**filters)

    def exclude(self, **filters):
        with self.thread_lock:
            self._check_scope(filters)

            manager = self.model.objects
            if not filters:
                queryset = manager.all()
            else:
                queryset = manager.exclude(**filters)

            if self.order:
                queryset = queryset.order_by(*self.order)

            if self.limit:
                queryset = queryset[:self.limit]

            return queryset


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

    def keep(self):
        # Override in subclass
        return []

    def keep_relations(self):
        # Override in subclass
        return {}


    def create(self, key, **values):
        values[self.key()] = key
        self._check_scope(values)
        with self.thread_lock:
            instance = self.model(**values)
        return instance

    def store(self, key, **values):
        filters = { self.key(): key }
        instance = self.retrieve(key, **filters)
        created = False

        if not instance:
            instance = self.create(key, **filters)
            created = True

        values = data.normalize_dict(values)

        for field, value in values.items():
            setattr(instance, field, value)

        instance.save()
        return (instance, created)

    def delete(self, key, **filters):
        if key not in data.ensure_list(self.keep()):
            filters[self.key()] = key
            return self.clear(**filters)
        else:
            raise RestrictedError("Removal of {} {} is restricted".format(self.model.__name__.lower(), key))

    def clear(self, **filters):
        queryset = self.query(**filters)

        with self.thread_lock:
            keep_list = self.keep()
            if keep_list:
                queryset = queryset.exclude(**{
                    "{}__in".format(self.key()): data.ensure_list(keep_list)
                })
            deleted, del_per_type = queryset.delete()

            if deleted:
                return True
            return False


    def get_field_created_display(self, instance, value, short):
        return localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")

    def get_field_updated_display(self, instance, value, short):
        return localtime(value).strftime("%Y-%m-%d %H:%M:%S %Z")
