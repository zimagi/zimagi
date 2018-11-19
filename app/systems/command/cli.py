from collections import OrderedDict, defaultdict

from django.core import management
from django.core.management import ManagementUtility, find_commands, load_command_class
from django.core.management.color import color_style
from django.core.management.base import (
    BaseCommand, CommandError, CommandParser, handle_default_options,
)

import os
import functools


@functools.lru_cache(maxsize=None)
def get_commands():
    """
    Return a dictionary mapping command names to their callback applications.

    Look for a management.commands package in django.core, and in each
    installed application -- if a commands package exists, register all
    commands in that package.

    Core commands are always included. If a settings module has been
    specified, also include user-defined commands.

    The dictionary is in the format {command_name: app_name}. Key-value
    pairs from this dictionary can then be used in calls to
    load_command_class(app_name, command_name)

    If a specific version of a command must be loaded (e.g., with the
    startapp command), the instantiated module can be placed in the
    dictionary in place of the application name.

    The dictionary is cached on the first call and reused on subsequent
    calls.
    """
    init_commands = management.get_commands()
    include_commands = {
        'django.core': [
            'check',
            'dbshell',
            'inspectdb',
            'showmigrations',
            'makemigrations',
            'migrate'
        ],
        'django.contrib.contenttypes': []
    }
    commands = {}
    
    for command, namespace in init_commands.items():
        if namespace not in include_commands or command in include_commands[namespace]:
            commands[command] = namespace

    return commands


class AppManagementUtility(ManagementUtility):
    
    def __init__(self, argv=None):
        super(AppManagementUtility, self).__init__(argv)
        self.prog_name = 'hcp'


    def main_help_text(self, commands_only=False):
        if commands_only:
            usage = sorted(get_commands())
        else:
            usage = [
                "",
                "Type '%s help <subcommand>' for help on a specific subcommand." % self.prog_name,
                "",
                "Available subcommands:",
            ]
            commands_dict = defaultdict(lambda: [])
            for name, app in get_commands().items():
                if app == 'django.core':
                    app = 'django'
                else:
                    app = app.rpartition('.')[-1]
 
                commands_dict[app].append(name)
 
            style = color_style()
            for app in sorted(commands_dict):
                usage.append("")
                usage.append(style.NOTICE("[%s]" % app))
 
                for name in sorted(commands_dict[app]):
                    usage.append("    %s" % name)
 
            if self.settings_exception is not None:
                usage.append(style.NOTICE(
                    "Note that only Django core commands are listed "
                    "as settings are not properly configured (error: %s)."
                    % self.settings_exception))
 
        return '\n'.join(usage)


    def fetch_command(self, subcommand):
        """
        Try to fetch the given subcommand, printing a message with the
        appropriate command called from the command line (usually
        "django-admin" or "manage.py") if it can't be found.
        """
        commands = get_commands()
        try:
            app_name = commands[subcommand]
        except KeyError:
            if os.environ.get('DJANGO_SETTINGS_MODULE'):
                settings.INSTALLED_APPS
            else:
                sys.stderr.write("No Django settings specified.\n")
             
            possible_matches = get_close_matches(subcommand, commands)
            sys.stderr.write('Unknown command: %r' % subcommand)
             
            if possible_matches:
                sys.stderr.write('. Did you mean %s?' % possible_matches[0])
             
            sys.stderr.write("\nType '%s help' for usage.\n" % self.prog_name)
            sys.exit(1)
         
        if isinstance(app_name, BaseCommand):
            klass = app_name
        else:
            klass = load_command_class(app_name, subcommand)
 
        return klass


    def autocomplete(self):
        """
        Output completion suggestions for BASH.

        The output of this function is passed to BASH's `COMREPLY` variable and
        treated as completion suggestions. `COMREPLY` expects a space
        separated string as the result.

        The `COMP_WORDS` and `COMP_CWORD` BASH environment variables are used
        to get information about the cli input. Please refer to the BASH
        man-page for more information about this variables.

        Subcommand options are saved as pairs. A pair consists of
        the long option string (e.g. '--exclude') and a boolean
        value indicating if the option requires arguments. When printing to
        stdout, an equal sign is appended to options which require arguments.

        Note: If debugging this function, it is recommended to write the debug
        output in a separate file. Otherwise the debug output will be treated
        and formatted as potential completion suggestions.
        """
        if 'DJANGO_AUTO_COMPLETE' not in os.environ:
            return
 
        cwords = os.environ['COMP_WORDS'].split()[1:]
        cword = int(os.environ['COMP_CWORD'])
 
        try:
            curr = cwords[cword - 1]
        except IndexError:
            curr = ''
 
        subcommands = [*get_commands(), 'help']
        options = [('--help', False)]
 
        if cword == 1:
            print(' '.join(sorted(filter(lambda x: x.startswith(curr), subcommands))))
         
        elif cwords[0] in subcommands and cwords[0] != 'help':
            subcommand_cls = self.fetch_command(cwords[0])
 
            if cwords[0] in ('dumpdata', 'sqlmigrate', 'sqlsequencereset', 'test'):
                try:
                    app_configs = apps.get_app_configs()
                    options.extend((app_config.label, 0) for app_config in app_configs)
                except ImportError:
                    pass
 
            parser = subcommand_cls.create_parser('', cwords[0])
            options.extend(
                (min(s_opt.option_strings), s_opt.nargs != 0)
                for s_opt in parser._actions if s_opt.option_strings
            )
            prev_opts = {x.split('=')[0] for x in cwords[1:cword - 1]}
            options = (opt for opt in options if opt[0] not in prev_opts)
 
            options = sorted((k, v) for k, v in options if k.startswith(curr))
            for opt_label, require_arg in options:
                if require_arg:
                    opt_label += '='
 
                print(opt_label)
         
        sys.exit(0)


def execute_from_command_line(argv=None):
    utility = AppManagementUtility(argv)
    utility.execute()
