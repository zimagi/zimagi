from django.conf import settings

from systems.command.base import command_list, AppBaseCommand
from systems.command.registry import get_commands, CommandRegistry
from systems.command.types import environment, router
from utility.text import wrap

class Command(
    environment.EnvironmentActionCommand
):
    def display_header(self):
        return False

    def parse(self):
        self.parse_variables('command_name', True, str, "command name")

    def exec(self):
        command = self.options.get('command_name', [])
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
        def process_subcommands(name, command, usage, width, init_indent, indent):
            if isinstance(command, router.RouterCommand):
                for info in command.get_subcommands():
                    full_name = "{} {}".format(name, info[0])
                    subcommand = command.subcommands[info[0]]
                    usage.extend(wrap(
                        subcommand.get_description(True), width,
                        init_indent = "{:{width}}{}  -  ".format(' ', self.command_color(full_name), width = init_indent),
                        init_style = self.header_color(),
                        indent      = "".ljust(indent)
                    ))
                    process_subcommands(full_name, subcommand, usage, width - 5, init_indent + 5, indent + 5)

        for name, app in get_commands().items():
            if app != 'django.core' and name != 'help':
                command = self.registry.fetch_command(name)

                if isinstance(command, AppBaseCommand):
                    priority = command.get_priority()

                    if priority not in commands:
                        commands[priority] = {}

                    command_help = wrap(
                        command.get_description(True), settings.DISPLAY_WIDTH,
                        init_indent = " {}  -  ".format(self.command_color(name)),
                        init_style = self.header_color(),
                        indent      = " {:5}".format(' ')
                    )
                    process_subcommands(name, command, command_help, settings.DISPLAY_WIDTH - 5, 6, 11)
                    commands[priority][name] = command_help

        for priority in sorted(commands.keys(), reverse = True):
            for name, command_help in commands[priority].items():
                usage.extend(command_help)

        self.info('\n'.join(usage))


    def render_command(self, command):
        command = self.registry.find_command(command, self)
        command.print_help()
