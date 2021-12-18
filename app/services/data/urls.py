
from django.conf.urls import include, url
from rest_framework.schemas import get_schema_view
from rest_framework import permissions

from systems.api import views as shared_views
from systems.api.data import routers, views, schema, renderers


status_view = shared_views.Status.as_view(
    permission_classes = [ permissions.AllowAny ],
    schema = schema.StatusSchema()
)

urlpatterns = [
    url(r'^status/?$', status_view),
    url(r'^download/(?P<name>[^\/]+)/?$', views.DataSet.as_view()),
    url(r'^', include(routers.DataAPIRouter().urls)),
    url('^$', get_schema_view(
        title = 'Zimagi Data API',
        generator_class = schema.DataSchemaGenerator,
        renderer_classes = [ renderers.DataSchemaJSONRenderer ],
        permission_classes = [ permissions.AllowAny ]
    ))
]
