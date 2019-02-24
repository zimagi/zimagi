from systems.command import types
#from . import _config as config


class Command(types.ConfigRouterCommand):

    def get_command_name(self):
        return 'config'

    #def get_subcommands(self):
    #    return (
    #        ('list', config.ListCommand),
    #        ('get', config.GetCommand),
    #        ('set', config.SetCommand),
    #        ('rm', config.RemoveCommand),
    #        ('clear', config.ClearCommand),
    #        ('group', config.GroupCommand)
    #    )
