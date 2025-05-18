from rest_framework import renderers
from systems.api.command.codecs import ZimagiJSONCodec
from systems.api.encoders import SafeJSONEncoder


class CommandSchemaJSONRenderer(renderers.BaseRenderer):
    media_type = "application/vnd.zimagi+json"

    def render(self, data, media_type=None, renderer_context=None):
        return ZimagiJSONCodec().encode(data, cls=SafeJSONEncoder, indent=int(renderer_context.get("indent", 2)))
