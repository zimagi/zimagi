
from django.conf.urls import include, url

from rest_framework import renderers
from rest_framework.schemas import get_schema_view

from systems.api import routers
from systems.api.schema import generator


urlpatterns = [
    url(r'^', include(routers.CommandAPIRouter().urls)),
    url('^$', get_schema_view(
        title = "CE API",
        generator_class = generator.CommandSchemaGenerator,
        renderer_classes = [ renderers.CoreJSONRenderer ]
    ))
]
