from django.conf import settings
from django.urls import include, re_path
from rest_framework import permissions

from systems.api import views as shared_views
from systems.api.command import schema
from systems.forms import routers


status_view = shared_views.Status.as_view(
    permission_classes = [ permissions.AllowAny ],
    schema = schema.StatusSchema(),
    encryption = False
)

urlpatterns = [
    re_path(r'^status/?$', status_view),
    re_path(r'^', include(routers.FormRouter().urls))
]
