from rest_framework import renderers
from systems.api.encoders import SafeJSONEncoder
from utility.data import dump_json


class DataSchemaJSONRenderer(renderers.JSONOpenAPIRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        indent = int(renderer_context.get("indent", 2))
        return dump_json(data, cls=SafeJSONEncoder, indent=indent).encode("utf-8")
