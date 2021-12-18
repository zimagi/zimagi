from rest_framework import renderers
from rest_framework.compat import coreapi

from systems.api.encoders import SafeJSONEncoder


class CommandSchemaJSONRenderer(renderers.CoreJSONRenderer):

    def render(self, data, media_type = None, renderer_context = None):
        indent = int(renderer_context.get('indent', 2))
        codec = coreapi.codecs.CoreJSONCodec()
        return codec.dump(data, cls = SafeJSONEncoder, indent = indent)
