from datetime import datetime

from rest_framework.serializers import HyperlinkedModelSerializer

import re


class BaseSerializer(HyperlinkedModelSerializer):
    pass


class BaseUpdateSerializer(BaseSerializer):
    pass