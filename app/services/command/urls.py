from django.conf import settings
from django.urls import include, re_path
from rest_framework.schemas import get_schema_view
from rest_framework import permissions

from systems.api import views as shared_views
from systems.api.command import routers, schema, renderers


status_view = shared_views.Status.as_view(
    permission_classes = [ permissions.AllowAny ],
    schema = schema.StatusSchema(),
    encryption = settings.ENCRYPT_COMMAND_API
)

urlpatterns = [
    re_path(r'^status/?$', status_view),
    re_path(r'^', include(routers.CommandAPIRouter().urls)),
    re_path('^$', get_schema_view(
        title = 'Zimagi Command API',
        generator_class = schema.CommandSchemaGenerator,
        renderer_classes = [ renderers.CommandSchemaJSONRenderer ],
        permission_classes = [ permissions.AllowAny ]
    ))
]
