from systems.command import types


def Router(parent, commands):

    def _get_subcommands(self):
        return commands
    
    return type('RouterCommand', (parent,), {
        'get_subcommands': _get_subcommands
    })
