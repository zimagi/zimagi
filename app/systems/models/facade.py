from collections import OrderedDict
from functools import lru_cache

from django.conf import settings
from django.db.models import fields, Count, Avg, Min, Max, Sum
from django.db.models.fields import NOT_PROVIDED, Field
from django.db.models.fields.related import RelatedField, ForeignKey, OneToOneField, ManyToManyField
from django.db.models.fields.reverse_related import ForeignObjectRel, ManyToOneRel, OneToOneRel, ManyToManyRel
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.utils.timezone import localtime

from systems.models.aggregates import Concat
from utility import query, data, terminal

import binascii
import os
import re
import pandas
import hashlib


class ScopeError(Exception):
    pass

class AccessError(Exception):
    pass

class RestrictedError(Exception):
    pass


class ModelFacade(terminal.TerminalMixin):

    _viewset = {}


    def __init__(self, cls):
        super().__init__()

        self.model = cls

        self.name = self.meta.verbose_name.replace(' ', '_')
        self.plural = self.meta.verbose_name_plural.replace(' ', '_')

        if self.meta.pk.name.endswith('_ptr') and self.meta.parents:
            self.pk = list(self.meta.parents.keys())[0].facade.pk
        else:
            self.pk = self.meta.pk.name

        self.required = []
        self.optional = []
        self.fields = []
        self.field_map = {}
        self._field_type_map = None

        self._scope = {}
        self.order = None
        self.limit = None
        self.annotations = {}

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


    def get_viewset(self):
        from systems.api.data.views import DataViewSet
        if self.name not in self._viewset:
            self._viewset[self.name] = DataViewSet(self)
        return self._viewset[self.name]


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


    def get_field_type_index(self):
        # Override in subclass if needed (field_class_name: type_name)
        return {
            'BooleanField': 'bool',
            'NullBooleanField': 'bool',
            'CharField': 'text',
            'TextField': 'text',
            'SlugField': 'text',
            'EmailField': 'text',
            'GenericIPAddressField': 'text',
            'URLField': 'text',
            'CSVField': 'text',
            'AutoField': 'number',
            'SmallAutoField': 'number',
            'BigAutoField': 'number',
            'IntegerField': 'number',
            'SmallIntegerField': 'number',
            'BigIntegerField': 'number',
            'PositiveIntegerField': 'number',
            'PositiveSmallIntegerField': 'number',
            'DecimalField': 'number',
            'FloatField': 'number',
            'DurationField': 'number',
            'DateField': 'date',
            'DateTimeField': 'time',
            'TimeField': 'time'
        }

    def get_field_name_type_index(self):
        # Override in subclass (field_name: type_name)
        return {}

    @property
    def atomic_fields(self):
        return self._get_field_type_map('atomic')

    @property
    def meta_fields(self):
        return self._get_field_type_map('meta')

    @property
    def bool_fields(self):
        return self._get_field_type_map('bool')

    @property
    def text_fields(self):
        return self._get_field_type_map('text')

    @property
    def number_fields(self):
        return self._get_field_type_map('number')

    @property
    def date_fields(self):
        return self._get_field_type_map('date')

    @property
    def time_fields(self):
        return self._get_field_type_map('time')

    def _get_field_type_map(self, type):
        field_type_index = self.get_field_type_index()
        field_name_type_index = self.get_field_name_type_index()

        if not self._field_type_map:
            self._field_type_map = {
                'meta': [],
                'bool': [],
                'text': [],
                'number': [],
                'date': [],
                'time': [],
                'atomic': {}
            }
            for field_name, field in self.field_map.items():
                if not field.is_relation:
                    field_class_name = field.__class__.__name__
                    field_type = field_name_type_index.get(field_name, None)

                    if field_name in self.dynamic_fields:
                        self._field_type_map['meta'].append(field_name)
                    else:
                        if field_name in (self.pk, self.key(), 'created', 'updated'):
                            self._field_type_map['meta'].append(field_name)

                        if not field_type and field_class_name in field_type_index:
                            field_type = field_type_index[field_class_name]

                        if field_type and field_type in self._field_type_map:
                            self._field_type_map[field_type].append(field_name)

                    self._field_type_map['atomic'][field_name] = True

        if type == 'atomic':
            return list(self._field_type_map[type].keys())
        return self._field_type_map[type]


    def get_packages(self):
        packages = [
            settings.DB_PACKAGE_ALL_NAME,
            self.name
        ]
        packages.extend(self.get_children(True))
        return list(set(packages))

    def check_api_enabled(self):
        return False


    def hash(self, *args):
        return hashlib.sha256("-".join(sorted(args)).encode()).hexdigest()

    def tokenize(self, seed):
        return binascii.hexlify(seed).decode()

    def generate_token(self, size = 40):
        return self.tokenize(os.urandom(size))[:size]


    def key(self):
        # Override in subclass if model is scoped
        return self.pk


    @property
    @lru_cache(maxsize = None)
    def scope_fields(self):
        if getattr(self.meta, 'scope', None):
            return data.ensure_list(self.meta.scope)
        return []

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


    def set_scope(self, filters):
        self._scope = filters
        return self

    def get_scope(self):
        return self._scope

    def get_scope_name(self):
        return self.hash(*[ value for key, value in self.get_scope().items() ])

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
        for filter, value in self.get_scope().items():
            if not filter in filters:
                filters[filter] = value


    @lru_cache(maxsize = None)
    def get_children(self, recursive = False, process = 'all'):
        children = []
        for model in self.manager.index.get_models():
            model_fields = { f.name: f for f in model._meta.fields }
            fields = model.facade.scope_fields

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
            if field.name not in scope_fields and isinstance(field, (ForeignKey, ManyToManyField, OneToOneField)):
                if not field.name.endswith('_ptr'):
                    if isinstance(field, ManyToManyField):
                        multiple = True
                    elif isinstance(field, (ForeignKey, OneToOneField)):
                        multiple = False

                    relations[field.name] = {
                        'name': field.name,
                        'label': "{}{}".format(field.name.replace('_', ' ').title(), ' (M)' if multiple else ''),
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

                    if isinstance(field, OneToOneRel):
                        multiple = False
                    elif isinstance(field, (ManyToOneRel, ManyToManyRel)):
                        multiple = True

                    if name not in ('log', 'state'):
                        relations[field.name] = {
                            'name': field.name,
                            'label': "{}{}".format(field.name.replace('_', ' ').title(), ' (M)' if multiple else ''),
                            'model': field.related_model,
                            'field': field,
                            'multiple': multiple
                        }
        return relations

    @lru_cache(maxsize = None)
    def get_referenced_relations(self):
        scope_relations = {}
        for field in self.meta.get_fields():
            if field.name in self.scope_fields:
                scope_relations[field.name] = {
                    'name': field.name,
                    'label': field.name.replace('_', ' ').title(),
                    'model': field.related_model,
                    'field': field,
                    'multiple': False
                }
        return {
            **scope_relations,
            **self.get_relations()
        }

    @lru_cache(maxsize = None)
    def get_all_relations(self):
        return {
            **self.get_referenced_relations(),
            **self.get_reverse_relations()
        }


    @property
    def aggregator_map(self):
        return {
            'COUNT': {
                'class': Count,
                'types': ['bool', 'number', 'text', 'date', 'time'],
                'distinct': True
            },
            'AVG': {
                'class': Avg,
                'types': ['number'],
                'distinct': False
            },
            'SUM': {
                'class': Sum,
                'types': ['number'],
                'distinct': False
            },
            'MIN': {
                'class': Min,
                'types': ['number'],
                'distinct': False
            },
            'MAX': {
                'class': Max,
                'types': ['number'],
                'distinct': False
            },
            'CONCAT': {
                'class': Concat,
                'types': [],
                'distinct': True
            }
        }

    def get_aggregators(self, type):
        aggregators = []

        for function, info in self.aggregator_map.items():
            if type in info['types']:
                aggregators.append(function)

        return aggregators


    def set_annotations(self, **annotations):
        self.annotations = {}

        for field, info in annotations.items():
            params = {}
            if len(info) == 3 and isinstance(info[2], dict):
                params = info[2]

            self.annotations[field] = self.aggregator_map[info[0]]['class'](info[1], **params)

        return self


    def set_order(self, order):
        if order:
            self.order = [
                re.sub(r'^~', '-', x) for x in data.ensure_list(order)
            ]
        else:
            self.order = None

        return self

    def set_limit(self, limit):
        self.limit = limit
        return self


    def query(self, **filters):
        self._check_scope(filters)

        manager = self.model.objects

        if self.annotations:
            manager = manager.annotate(**self.annotations)

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


    def keys(self, queryset_function = None, **filters):
        queryset = self.query(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return queryset.values_list(self.key(), flat = True)

    def field_values(self, name, queryset_function = None, **filters):
        queryset = self.query(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return queryset.values_list(name, flat = True)

    def values(self, *fields, queryset_function = None, **filters):
        if not fields:
            fields = self.fields

        queryset = self.query(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return queryset.values(*fields)

    def dataframe(self, *fields, queryset_function = None, **filters):
        if not fields:
            fields = self.fields

        queryset = self.query(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return pandas.DataFrame.from_records(queryset.values_list(*fields), columns = fields)

    def count(self, queryset_function = None, **filters):
        queryset = self.query(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return queryset.count()


    def related(self, key, relation, **filters):
        instance = self.retrieve(key)
        queryset = None

        if instance:
            queryset = query.get_queryset(instance, relation)

            if queryset:
                if filters:
                    queryset = queryset.filter(**filters).distinct()
                else:
                    queryset = queryset.all()

        return queryset


    def retrieve_by_id(self, id):
        filters = {}
        self._check_scope(filters)

        try:
            filters[self.pk] = id
            data = self.model.objects.get(**filters)
        except self.model.DoesNotExist:
            return None
        return data

    def retrieve(self, key, **filters):
        self._check_scope(filters)
        try:
            filters[self.key()] = key
            data = self.model.objects.get(**filters)

        except self.model.DoesNotExist:
            return None

        except self.model.MultipleObjectsReturned:
            raise ScopeError("Scope missing from {} {} retrieval".format(self.name, key))

        return data


    def _ensure(self, command, reinit = False):
        # Added dynamically in the model index
        pass

    def ensure(self, command, reinit):
        # Override in subclass
        pass

    def keep(self, key = None):
        # Override in subclass
        return []

    def keep_relations(self):
        # Override in subclass
        return {}


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

        values = data.normalize_dict(values)

        for field, value in values.items():
            setattr(instance, field, value)

        instance.save()
        return (instance, created)

    def delete(self, key, **filters):
        if key not in data.ensure_list(self.keep(key)):
            filters[self.key()] = key
            return self.clear(**filters)
        else:
            raise RestrictedError("Removal of {} {} is restricted".format(self.model.__name__.lower(), key))

    def clear(self, **filters):
        queryset = self.query(**filters)
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
