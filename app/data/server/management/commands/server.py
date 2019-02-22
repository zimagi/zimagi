from systems.command.base import command_list
from systems.command import types, factory
from . import _server as server


class Command(types.ServerRouterCommand):

    def get_command_name(self):
        return 'server'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommands(
                types.ServerActionCommand, 'server',
                list_fields = (
                    ('name', 'Name'),
                    ('type', 'Type'),
                    ('subnet__network__name', 'Network'),
                    ('subnet__name', 'Subnet'),
                    ('ip', 'IP'),
                    ('user', 'User'),
                    ('status', 'Status')
                ),
                relations = ('groups', 'firewalls'),
                scopes = {
                    'network': '--network',
                    'subnet': '--subnet'
                }
            ),
            ('rotate', server.RotateCommand),
            ('ssh', server.SSHCommand),
            ('group', server.GroupCommand)
        )
