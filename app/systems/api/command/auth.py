from rest_framework import permissions

from systems.api.auth import APITokenAuthentication

import logging


logger = logging.getLogger(__name__)


class CommandAPITokenAuthentication(APITokenAuthentication):
    api_type = 'command_api'


class CommandPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return view.check_execute(request.user)
