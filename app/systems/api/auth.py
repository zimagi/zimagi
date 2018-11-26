
from rest_framework import permissions


class CommandPermission(permissions.BasePermission):
    """
    Global permission to check access to run commands.
    """
    def has_permission(self, request, view):
        return True