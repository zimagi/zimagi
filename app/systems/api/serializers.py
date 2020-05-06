from datetime import datetime

from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.serializers import HyperlinkedModelSerializer, PrimaryKeyRelatedField, SerializerMethodField

import re


class BaseSerializer(HyperlinkedModelSerializer):
    pass

class BaseUpdateSerializer(BaseSerializer):
    pass


def get_field_map(facade, dynamic = True):

    def get_dynamic_field(field_name):
        def _dynamic_display(self, instance):
            display_method = gettr(facade, "get_field_{}_display".format(field_name), None)
            if display_method:
                return display_method(instance, False)
            return None
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
    field_map = get_field_map(facade, False)

    if facade.pk != facade.key:
        field_map['Meta'].fields = [ facade.pk, facade.key(), 'api_url' ]
    else:
        field_map['Meta'].fields = [ facade.pk, 'api_url' ]

    return type('MetaSerializer', (BaseSerializer,), field_map)

def MetaSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields = facade.meta_fields + [ 'api_url' ]
    return type('MetaSerializer', (BaseSerializer,), field_map)

def SummarySerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields.append('api_url')
    return type('SummarySerializer', (BaseSerializer,), field_map)

def DetailSerializer(facade):
    field_map = get_related_field_map(facade)
    field_map.pop('api_url')
    return type('DetailSerializer', (BaseSerializer,), field_map)

def TestSerializer(facade):
    field_map = get_related_field_map(facade)
    field_map['Meta'].fields.append('api_url')
    return type('TestSerializer', (BaseSerializer,), field_map)


def get_update_field_map(facade):
    relations = facade.get_referenced_relations()
    field_map = {
        'Meta': type('Meta', (object,), {
            'model': facade.model,
            'fields': list(set(facade.atomic_fields) - set(facade.dynamic_fields))
        })
    }
    for field_name, info in relations.items():
        if getattr(info['model'], 'facade', None) and field_name not in facade.dynamic_fields:
            field_map[field_name] = PrimaryKeyRelatedField(
                many = info['multiple'],
                read_only = False,
                queryset = info['model'].facade.all()
            )
            field_map['Meta'].fields.append(field_name)

    return field_map


def CreateSerializer(facade):
    field_map = get_update_field_map(facade)
    return type('CreateSerializer', (BaseUpdateSerializer,), field_map)

def UpdateSerializer(facade):
    field_map = get_update_field_map(facade)
    field_map['Meta'].read_only_fields = [ facade.pk ]
    return type('UpdateSerializer', (BaseUpdateSerializer,), field_map)
