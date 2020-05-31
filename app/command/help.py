from django.conf import settings

from systems.command import router
from systems.command.index import Command
from utility.text import wrap


class Help(Command('help')):

    def exec(self):
        command = self.command_name
        if not command:
            self.render_overview()
        else:
            self.render_command(command)


    def render_overview(self):
        commands = {}
        usage = [
            "Type '{}' for help on a specific subcommand.".format(
                self.command_color("{} help <subcommand> ...".format(settings.APP_NAME))
            ),
            "",
            "Available subcommands:",
            ""
        ]
        def render_command(command, width, init_indent, indent):
            usage.extend(wrap(
                command.get_description(True), width,
                init_indent = "{:{width}}{}  -  ".format(' ', self.command_color(command.name), width = init_indent),
                init_style = self.header_color(),
                indent = "".ljust(indent)
            ))
            if isinstance(command, router.RouterCommand):
                for subcommand in command.get_subcommands():
                    render_command(subcommand, width - 5, init_indent + 5, indent + 5)

        for subcommand in self.manager.index.command_tree.get_subcommands():
            if subcommand.name != 'help':
                render_command(subcommand, settings.DISPLAY_WIDTH, 1, 5)

        self.info('\n'.join(usage))


    def render_command(self, command):
        command = self.manager.index.find_command(command, self)
        command.print_help()
