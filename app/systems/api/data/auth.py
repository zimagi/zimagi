import logging

from django.conf import settings
from rest_framework import exceptions, permissions
from systems.api.auth import APITokenAuthentication
from utility.data import ensure_list

logger = logging.getLogger(__name__)


class DataAPITokenAuthentication(APITokenAuthentication):
    api_type = "data_api"


class DataPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method not in ("GET", "OPTIONS", "HEAD", "POST", "PUT", "DELETE"):
            raise exceptions.MethodNotAllowed(request.method)

        if not getattr(view, "facade", None):
            # Schema view should be accessible
            return True

        model_name = view.facade.meta.data_name
        roles = settings.MANAGER.get_spec(f"data.{model_name}.roles")

        groups = ["admin"] + ensure_list(roles.get("edit", []))

        if request.method in ("GET", "OPTIONS", "HEAD"):
            if roles.get("view", None):
                groups.extend(ensure_list(roles["view"]))

            if "public" in groups:
                return True

        if not request.user:
            raise exceptions.AuthenticationFailed("Authentication credentials were not provided")

        return request.user.groups.filter(name__in=groups).exists()
