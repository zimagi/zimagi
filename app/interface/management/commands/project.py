from systems.command import types, factory


class Command(types.ProjectRouterCommand):

    def get_command_name(self):
        return 'project'

    def get_subcommands(self):
        return factory.ResourceCommands(
            types.ProjectActionCommand, 'project',
            list_fields = (
                ('name', 'Name'),
                ('type', 'Type'),
                ('remote', 'Remote'),
                ('reference', 'Reference')
            )
        )
