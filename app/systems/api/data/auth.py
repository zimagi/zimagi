from django.conf import settings
from rest_framework import permissions, exceptions

from systems.api.auth import APITokenAuthentication
from utility.data import ensure_list

import logging


logger = logging.getLogger(__name__)


class DataAPITokenAuthentication(APITokenAuthentication):
    api_type = 'data_api'


class DataPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method not in ('GET', 'OPTIONS', 'HEAD'):
            raise exceptions.MethodNotAllowed(request.method)

        if not getattr(view, 'queryset', None):
            # Schema view should be accessible
            return True

        model_name = view.queryset.model._meta.data_name
        roles = settings.MANAGER.get_spec('data.{}.roles'.format(model_name))

        groups = ['admin'] + ensure_list(roles.get('edit', []))
        if roles.get('view', None):
            groups.extend(ensure_list(roles['view']))

        if 'public' in groups:
            return True

        if not request.user:
            raise exceptions.AuthenticationFailed('Authentication credentials were not provided')

        return request.user.env_groups.filter(name__in = groups).exists()
