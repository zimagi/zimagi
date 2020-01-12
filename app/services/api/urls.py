
from django.conf.urls import include, url

from rest_framework import renderers
from rest_framework.schemas import get_schema_view

from systems.api import routers, views
from systems.api.schema import generator


urlpatterns = [
    url(r'^', include(routers.CommandAPIRouter().urls)),
    url(r'^status/?$', views.Status.as_view()),
    url('^$', get_schema_view(
        title = "MCMI API",
        generator_class = generator.CommandSchemaGenerator,
        renderer_classes = [ renderers.CoreJSONRenderer ]
    ))
]
