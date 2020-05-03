from datetime import datetime

from rest_framework.serializers import HyperlinkedModelSerializer

import re


class BaseSerializer(HyperlinkedModelSerializer):
    pass

class BaseUpdateSerializer(BaseSerializer):
    pass


def get_field_map(facade):
    field_map = {
        'Meta': type('Meta', {
            'model': facade.model,
            'fields': []
        })
    }
    # Initialize relation serializers

    return field_map


def MetaSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields = [] # Meta fields (identity and dates)
    return type('MetaSerializer', BaseSerializer, field_map)

def TestSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields = [] # Base + Relations + URL
    return type('TestSerializer', BaseSerializer, field_map)


def SummarySerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields = [] # Base + URL
    return type('SummarySerializer', BaseSerializer, field_map)

def DetailSerializer(facade):
    field_map = get_field_map(facade)
    field_map['Meta'].fields = [] # Base + Relations
    return type('DetailSerializer', BaseSerializer, field_map)


def get_update_field_map(facade):
    field_map = {
        'Meta': type('Meta', {
            'model': facade.model,
            'fields': []
        })
    }
    # Initialize relation ID serializers (char field)

    return field_map


def CreateSerializer(facade):
    field_map = get_update_field_map(facade)
    field_map['Meta'].fields = [] # Base + Relations
    return type('CreateSerializer', BaseUpdateSerializer, field_map)

def UpdateSerializer(facade):
    field_map = get_update_field_map(facade)
    field_map['Meta'].fields = [] # Base + Relations
    field_map['Meta'].read_only_fields = [ facade.pk ]
    return type('UpdateSerializer', BaseUpdateSerializer, field_map)
