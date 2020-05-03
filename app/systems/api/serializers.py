from datetime import datetime

from rest_framework.serializers import HyperlinkedModelSerializer

import re


class BaseSerializer(HyperlinkedModelSerializer):
    pass

class BaseUpdateSerializer(BaseSerializer):
    pass


def MetaSerializer(facade):
    return type('MetaSerializer', BaseSerializer, {})

def TestSerializer(facade):
    return type('TestSerializer', BaseSerializer, {})


def SummarySerializer(facade):
    return type('SummarySerializer', BaseSerializer, {})

def DetailSerializer(facade):
    return type('DetailSerializer', BaseSerializer, {})

def CreateSerializer(facade):
    return type('CreateSerializer', BaseUpdateSerializer, {})

def UpdateSerializer(facade):
    return type('UpdateSerializer', BaseUpdateSerializer, {})
