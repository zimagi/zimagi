from urllib.parse import urlencode
from django.urls import NoReverseMatch
from django.core.exceptions import ImproperlyConfigured
from rest_framework.fields import Field
from rest_framework.reverse import reverse

from utility.data import dump_json, load_json


class HyperlinkedRelatedField(Field):

    def __init__(self, facade, view_name, related_field, **kwargs):
        self.facade = facade
        self.view_name = view_name
        self.related_field = related_field

        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        request = self.context['request']

        try:
            base_url = reverse(self.view_name, request = request)
            url = "{}?{}".format(
                base_url,
                urlencode({ self.related_field: value.instance.pk })
            )

        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            if value in ('', None):
                value_string = {'': 'an empty string', None: 'None'}[value]
                msg += (
                    " WARNING: The value of the field on the model instance "
                    "was %s, which may be why it didn't match any "
                    "entries in your URL conf." % value_string
                )
            raise ImproperlyConfigured(msg % self.view_name)
        return url


class JSONDataField(Field):

    def to_representation(self, value):
        if isinstance(value, str) and value[0] in ('[', '{') and value[-1] in (']', '}'):
            return load_json(value)
        return value

    def to_internal_value(self, data):
        if not isinstance(data, str):
            return dump_json(data)
        return data
