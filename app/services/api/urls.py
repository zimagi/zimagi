
from django.conf.urls import include, url
from django.core.management import call_command

from rest_framework import renderers
from rest_framework.schemas import get_schema_view

from systems.api import routers
from systems.api.schema import generator
from utility.display import suppress_stdout


with suppress_stdout():
    call_command('migrate', interactive = False)


urlpatterns = [
    url(r'^', include(routers.CommandAPIRouter().urls)),
    url('^$', get_schema_view(
        title = "CE API",
        generator_class = generator.CommandSchemaGenerator,
        renderer_classes = [ renderers.CoreJSONRenderer ]
    ))
]
