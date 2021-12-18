from rest_framework import renderers

from .encoders import SafeJSONEncoder


class JSONRenderer(renderers.JSONRenderer):
    encoder_class = SafeJSONEncoder
