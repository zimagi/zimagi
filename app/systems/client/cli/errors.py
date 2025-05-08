from django.core.management.base import CommandError


class CommandNetworkError(CommandError):
    pass


class CommandNotFoundError(CommandError):
    pass


class CommandMessageError(CommandError):
    pass


class CommandAbort(CommandError):
    pass
