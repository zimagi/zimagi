
from django.conf.urls import include, url
from django.views.decorators.cache import cache_page

from rest_framework.schemas import get_schema_view

from systems.api import routers, views
from systems.api.schema import generators, renderers


urlpatterns = [
    url(r'^status/?$', views.Status.as_view()),
    url(r'^', include(routers.CommandAPIRouter().urls)),
    url('^$', cache_page(None, cache = 'api')(get_schema_view(
        title = 'MCMI COMMAND API',
        generator_class = generators.CommandSchemaGenerator,
        renderer_classes = [ renderers.CommandSchemaJSONRenderer ]
    )))
]
