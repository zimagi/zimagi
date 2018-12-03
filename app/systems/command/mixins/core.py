
from systems.command import args
from data.environment import models
from utility.text import wrap


class CoreMixin(object):

    def parse_verbosity(self):
        name = 'verbosity'
        help_text = "\n".join(wrap("verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output", 40))

        self.add_schema_field(name, 
            args.parse_option(self.parser, 
                name, ('-v', '--verbosity'),
                int, help_text, 
                1, (0, 1, 2, 3)
            ), 
            True
        )

    @property
    def verbosity(self):
        return self.options['verbosity']


    def parse_color(self):
        name = 'no_color'
        help_text = "don't colorize the command output."

        self.add_schema_field(name, 
            args.parse_bool(self.parser, name, '--no-color', help_text), 
            True
        )

    @property
    def no_color(self):
        return self.options['no_color']
