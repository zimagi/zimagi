from rest_framework import renderers
from systems.api.encoders import SafeJSONEncoder
from systems.api.command.codecs import ZimagiJSONCodec


class CommandSchemaJSONRenderer(renderers.BaseRenderer):

    media_type = 'application/zimagi+json'


    def render(self, data, media_type = None, renderer_context = None):
        return ZimagiJSONCodec().encode(data,
            cls = SafeJSONEncoder,
            indent = int(renderer_context.get('indent', 2))
        )
