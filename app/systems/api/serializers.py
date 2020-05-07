from datetime import datetime

from rest_framework import fields
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.serializers import Serializer, HyperlinkedModelSerializer, PrimaryKeyRelatedField, SerializerMethodField

import re


class BaseSerializer(Serializer):
    pass

class BaseItemSerializer(HyperlinkedModelSerializer):
    pass


def get_field_map(facade, dynamic = True):

    def get_dynamic_field(field_name):
        def _dynamic_display(self, instance):
            return getattr(instance, field_name, None)
        return _dynamic_display

    field_map = {
        'api_url': HyperlinkedIdentityField(
            view_name = "{}-detail".format(facade.name),
            lookup_field = facade.pk
        ),
        'Meta': type('Meta', (object,), {
            'model': facade.model,
            'fields': list(set(facade.atomic_fields) - set(facade.dynamic_fields))
        })
    }
    if dynamic:
        for field_name in facade.dynamic_fields:
            field_map[field_name] = SerializerMethodField()
            field_map["get_{}".format(field_name)] = get_dynamic_field(field_name)
            field_map['Meta'].fields.append(field_name)

    return field_map

def get_related_field_map(facade, dynamic = True):
    relations = facade.get_referenced_relations()
    field_map = get_field_map(facade, dynamic)

    for field_name, info in relations.items():
        if getattr(info['model'], 'facade', None):
            field_map[field_name] = LinkSerializer(info['model'].facade)(many = info['multiple'])
            field_map['Meta'].fields.append(field_name)

    return field_map


def LinkSerializer(facade):
    class_name = "{}LinkSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = get_field_map(facade, False)

    if facade.pk != facade.key:
        field_map['Meta'].fields = [ facade.pk, facade.key(), 'api_url' ]
    else:
        field_map['Meta'].fields = [ facade.pk, 'api_url' ]

    serializer = type(class_name, (BaseItemSerializer,), field_map)
    globals()[class_name] = serializer
    return serializer

def MetaSerializer(facade):
    class_name = "{}MetaSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = get_field_map(facade)
    field_map['Meta'].fields = facade.meta_fields + [ 'api_url' ]

    serializer = type(class_name, (BaseItemSerializer,), field_map)
    globals()[class_name] = serializer
    return serializer

def SummarySerializer(facade):
    class_name = "{}SummarySerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = get_field_map(facade)
    field_map['Meta'].fields.append('api_url')

    serializer = type(class_name, (BaseItemSerializer,), field_map)
    globals()[class_name] = serializer
    return serializer

def DetailSerializer(facade):
    class_name = "{}DetailSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = get_related_field_map(facade)
    field_map.pop('api_url')

    serializer = type(class_name, (BaseItemSerializer,), field_map)
    globals()[class_name] = serializer
    return serializer

def TestSerializer(facade):
    class_name = "{}TestSerializer".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = get_related_field_map(facade)
    field_map['Meta'].fields.append('api_url')

    serializer = type(class_name, (BaseItemSerializer,), field_map)
    globals()[class_name] = serializer
    return serializer


class ValuesSerializer(BaseSerializer):
    count = fields.IntegerField(min_value = 0)
    results = fields.ListField(allow_empty = True)

class CountSerializer(BaseSerializer):
    count = fields.IntegerField(min_value = 0)
