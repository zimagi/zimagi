
from django.conf.urls import include, url

from rest_framework.schemas import get_schema_view

from systems.api import routers, views
from systems.api.schema import generators, renderers


urlpatterns = [
    url(r'^status/?$', views.Status.as_view()),
    url(r'^', include(routers.DataAPIRouter().urls)),
    url('^$', get_schema_view(
        title = 'Zimagi Data API',
        generator_class = generators.DataSchemaGenerator,
        renderer_classes = [ renderers.DataSchemaJSONRenderer ]
    ))
]
