from django.conf import settings
from django.urls import include, path, re_path
from rest_framework import permissions
from rest_framework.schemas import get_schema_view
from systems.api import views as shared_views
from systems.api.data import renderers, routers, schema, views

status_view = shared_views.Status.as_view(permission_classes=[permissions.AllowAny], encryption=settings.ENCRYPT_DATA_API)

urlpatterns = [
    re_path(r"^status/?$", status_view),
    re_path(r"^schema/(?P<path>.+)/?$", views.PathSchema.as_view()),
    re_path(r"^download/(?P<name>[^\/]+)/?$", views.DataSet.as_view()),
    path("", include(routers.DataAPIRouter().urls)),
    path(
        "",
        get_schema_view(
            title="Zimagi Data API",
            description="Modular Data Integration, Distributed Processsing, and API Distribution Platform",
            version=settings.VERSION,
            generator_class=schema.DataSchemaGenerator,
            renderer_classes=[renderers.DataSchemaJSONRenderer],
            permission_classes=[permissions.AllowAny],
        ),
    ),
]
