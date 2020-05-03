from datetime import datetime

from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.serializers import HyperlinkedModelSerializer

import re


class BaseSerializer(HyperlinkedModelSerializer):
    pass

class BaseUpdateSerializer(BaseSerializer):
    pass


def get_field_map(facade):
    field_map = {
        'api_url': HyperlinkedIdentityField(
            view_name = "{}-detail".format(facade.name),
            lookup_field = facade.pk
        )
        'Meta': type('Meta', {
            'model': facade.model,
            'fields': facade.atomic_fields
        })
    }
    # Initialize relation link serializers
    for field_name, info in facade.get_referenced_relations().items():
        pass

    return field_map


def LinkSerializer(facade):
    field_map = get_field_map(facade)

    if facade.pk != facade.key:
        field_map['Meta'].fields = [facade.pk, facade.key, 'api_url']
    else:
        field_map['Meta'].fields = [facade.pk, 'api_url']

    return type('MetaSerializer', BaseSerializer, field_map)

def MetaSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields = [] # Meta fields (identity and dates)
    return type('MetaSerializer', BaseSerializer, field_map)

def TestSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields.extend(facade.get_referenced_relations().keys() + ['api_url'])
    return type('TestSerializer', BaseSerializer, field_map)


def SummarySerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields.append('api_url')
    return type('SummarySerializer', BaseSerializer, field_map)

def DetailSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields.extend(facade.get_referenced_relations().keys())
    return type('DetailSerializer', BaseSerializer, field_map)


def get_update_field_map(facade):
    field_map = {
        'Meta': type('Meta', {
            'model': facade.model,
            'fields': facade.atomic_fields
        })
    }
    # Initialize relation ID serializers (char field)
    for field_name, info in facade.get_referenced_relations().items():
        pass

    return field_map


def CreateSerializer(facade):
    field_map = get_update_field_map(facade)
    field_map['Meta'].fields.extend(facade.get_referenced_relations().keys())
    return type('CreateSerializer', BaseUpdateSerializer, field_map)

def UpdateSerializer(facade):
    field_map = get_update_field_map(facade)
    field_map['Meta'].fields.extend(facade.get_referenced_relations().keys())
    field_map['Meta'].read_only_fields = [ facade.pk ]
    return type('UpdateSerializer', BaseUpdateSerializer, field_map)
