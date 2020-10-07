from datetime import datetime

from rest_framework import fields
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.serializers import Serializer, HyperlinkedModelSerializer, PrimaryKeyRelatedField, SerializerMethodField

import re


class BaseSerializer(Serializer):
    pass

class BaseItemSerializer(HyperlinkedModelSerializer):

    @property
    def view(self):
        return self._context.get('view', None)

    @property
    def view_request(self):
        return self._context.get('request', None)

    @property
    def view_format(self):
        return self._context.get('format', None)


def get_field_map(facade, fields = None, api_url = True, dynamic = True):

    def get_dynamic_field(field_name):
        def _dynamic_display(self, instance):
            value = getattr(instance, field_name, None)
            if value is None or '<locals>.RelatedManager' in str(type(value)):
                value = None
                display_function = getattr(facade, "get_field_{}_display".format(field_name), None)
                if display_function:
                    value = facade.raw_text(display_function(instance, None, False))
            return value

        return _dynamic_display

    if fields is None:
        fields = list(set(facade.atomic_fields) - set(facade.dynamic_fields))

    field_map = {
        'Meta': type('Meta', (object,), {
            'model': facade.model,
            'fields': fields
        })
    }
    if api_url or 'api_url' in fields:
        field_map['api_url'] = HyperlinkedIdentityField(
            view_name = "{}-detail".format(facade.name.replace('_', '')),
            lookup_field = facade.pk
        )
        field_map['Meta'].fields.append('api_url')
    if dynamic:
        for field_name in facade.dynamic_fields:
            field_map[field_name] = SerializerMethodField()
            field_map["get_{}".format(field_name)] = get_dynamic_field(field_name)
            field_map['Meta'].fields.append(field_name)

    return field_map

def get_related_field_map(facade, fields = None, api_url = True, dynamic = True):
    relations = facade.get_all_relations()
    field_map = get_field_map(facade,
        fields = fields,
        api_url = api_url,
        dynamic = dynamic
    )
    for field_name, info in relations.items():
        if getattr(info['model'], 'facade', None):
            field_map[field_name] = LinkSerializer(info['model'].facade)(many = info['multiple'])
            field_map['Meta'].fields.append(field_name)

    return field_map


def LinkSerializer(facade):
    class_name = "{}LinkSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    serializer = type(class_name, (BaseItemSerializer,), get_field_map(
        facade,
        fields = [ facade.pk, facade.key() ] if facade.pk != facade.key() else [ facade.pk ],
        api_url = True,
        dynamic = False
    ))
    globals()[class_name] = serializer
    return serializer

def MetaSerializer(facade):
    class_name = "{}MetaSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    serializer = type(class_name, (BaseItemSerializer,), get_field_map(
        facade,
        fields = facade.meta_fields,
        api_url = True,
        dynamic = True
    ))
    globals()[class_name] = serializer
    return serializer

def SummarySerializer(facade):
    class_name = "{}SummarySerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    serializer = type(class_name, (BaseItemSerializer,), get_field_map(
        facade,
        api_url = True,
        dynamic = True
    ))
    globals()[class_name] = serializer
    return serializer

def DetailSerializer(facade):
    class_name = "{}DetailSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    serializer = type(class_name, (BaseItemSerializer,), get_related_field_map(
        facade,
        api_url = False,
        dynamic = True
    ))
    globals()[class_name] = serializer
    return serializer

def TestSerializer(facade):
    class_name = "{}TestSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    serializer = type(class_name, (BaseItemSerializer,), get_related_field_map(
        facade,
        api_url = True,
        dynamic = True
    ))
    globals()[class_name] = serializer
    return serializer


class ValuesSerializer(BaseSerializer):
    count = fields.IntegerField(min_value = 0)
    results = fields.ListField(allow_empty = True)

class CountSerializer(BaseSerializer):
    count = fields.IntegerField(min_value = 0)
