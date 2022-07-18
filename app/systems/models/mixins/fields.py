from functools import lru_cache
from collections import OrderedDict

from django.conf import settings
from django.db.models.fields import NOT_PROVIDED, Field
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor

from utility.data import ensure_list

import re


class ModelFacadeFieldMixin(object):

    def __init__(self):
        super().__init__()

        if self.meta.pk.name.endswith('_ptr') and self.meta.parents:
            self.pk = list(self.meta.parents.keys())[0].facade.pk
        else:
            self.pk = self.meta.pk.name

        self.fields   = []
        self.required_fields = []
        self.optional_fields = []

        for field in self.field_instances:
            if field.name != self.pk and field.name != self.key():
                if (not field.null
                    and field.blank == False
                    and field.default == NOT_PROVIDED):
                    self.required_fields.append(field.name)
                else:
                    self.optional_fields.append(field.name)

            if field.name not in self.fields:
                self.fields.append(field.name)


    def key(self):
        # Override in subclass if model is scoped
        return self.pk


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
    @lru_cache(maxsize = None)
    def system_field_instances(self):
        fields = []
        for field in self.field_instances:
            if not field.editable:
                fields.append(field)
        return fields

    @property
    @lru_cache(maxsize = None)
    def field_index(self):
        return { field.name: field for field in self.meta.get_fields() }


    @property
    def dynamic_fields(self):
        if getattr(self.meta, 'dynamic_fields', None):
            return ensure_list(self.meta.dynamic_fields)
        return []

    @property
    def query_fields(self):
        fields = set(list(self.fields) + list(self.get_all_relations().keys()))
        return [ x for x in fields if x not in self.dynamic_fields ]

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


    @property
    @lru_cache(maxsize = None)
    def scope_fields(self):
        if getattr(self.meta, 'scope', None):
            return ensure_list(self.meta.scope)
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


    def check_field_related(self, field):
        return isinstance(field, (RelatedField, ForeignObjectRel))

    def get_field_default(self, field):
        if field.default == NOT_PROVIDED:
            return None
        return field.default


    def _parse_fields(self, fields):
        query_fields = []

        for field in fields:
            query_fields.append(re.sub(r'\.+', '__', field))

        return query_fields


    def _get_field_type_map(self, type):
        field_type_index = {
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
            'TimeField': 'time',
            **settings.FIELD_TYPE_MAP
        }
        if not getattr(self, '_field_type_map', None):
            self._field_type_map = {
                'meta': [],
                'bool': [],
                'text': [],
                'number': [],
                'date': [],
                'time': [],
                'atomic': {}
            }
            for field_name, field in self.field_index.items():
                if not field.is_relation:
                    field_class_name = field.__class__.__name__

                    if field_name in (self.pk, self.key(), 'created', 'updated'):
                        self._field_type_map['meta'].append(field_name)

                    if field_class_name in field_type_index:
                        field_type = field_type_index[field_class_name]

                    if field_type and field_type in self._field_type_map:
                        self._field_type_map[field_type].append(field_name)

                    self._field_type_map['atomic'][field_name] = True

        if type == 'atomic':
            return list(self._field_type_map[type].keys())
        return self._field_type_map[type]