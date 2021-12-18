from rest_framework import renderers

from systems.api.encoders import SafeJSONEncoder

import json


class DataSchemaJSONRenderer(renderers.JSONOpenAPIRenderer):

    def render(self, data, media_type = None, renderer_context = None):
        indent = int(renderer_context.get('indent', 2))
        return json.dumps(data, cls = SafeJSONEncoder, indent = indent).encode('UTF-8')
