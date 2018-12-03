
from rest_framework import permissions


class CommandPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        auth_method = getattr(view, 'groups_allowed', None)

        if auth_method and callable(auth_method):
            groups = view.groups_allowed()

            if not groups:
                return True

            return request.user.groups.filter(name__in=groups).exists()
        else:
            return True
