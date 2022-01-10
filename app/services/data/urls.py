from django.conf import settings
from django.urls import include, re_path
from rest_framework.schemas import get_schema_view
from rest_framework import permissions

from systems.api import views as shared_views
from systems.api.data import routers, views, schema, renderers


status_view = shared_views.Status.as_view(
    permission_classes = [ permissions.AllowAny ],
    schema = schema.StatusSchema(),
    encryption = settings.ENCRYPT_DATA_API
)

urlpatterns = [
    re_path(r'^status/?$', status_view),
    re_path(r'^download/(?P<name>[^\/]+)/?$', views.DataSet.as_view()),
    re_path(r'^', include(routers.DataAPIRouter().urls)),
    re_path('^$', get_schema_view(
        title = 'Zimagi Data API',
        generator_class = schema.DataSchemaGenerator,
        renderer_classes = [ renderers.DataSchemaJSONRenderer ],
        permission_classes = [ permissions.AllowAny ]
    ))
]
