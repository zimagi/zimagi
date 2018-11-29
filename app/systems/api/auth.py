
from rest_framework import permissions


class CommandPermission(permissions.BasePermission):
    
    def has_permission(self, request, view):
        groups = view.groups_allowed()

        if not groups:
            return True

        return request.user.groups.filter(name__in=groups).exists()
