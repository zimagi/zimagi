from rest_framework import renderers
from rest_framework.compat import coreapi
from rest_framework.utils import encoders

import json
import datetime


class SafeJSONEncoder(encoders.JSONEncoder):

    def default(self, obj):
        try:
            return super().default(obj)
        except Exception as e:
            return str(obj)


class DataJSONRenderer(renderers.JSONRenderer):
    encoder_class = SafeJSONEncoder


class CommandSchemaJSONRenderer(renderers.CoreJSONRenderer):

    def render(self, data, media_type = None, renderer_context = None):
        indent = bool(renderer_context.get('indent', 2))
        codec = coreapi.codecs.CoreJSONCodec()
        return codec.dump(data, cls = SafeJSONEncoder, indent = indent)


class DataSchemaJSONRenderer(renderers.JSONOpenAPIRenderer):

    def render(self, data, media_type = None, renderer_context = None):
        indent = bool(renderer_context.get('indent', 2))
        return json.dumps(data, cls = SafeJSONEncoder, indent = indent).encode('utf-8')
