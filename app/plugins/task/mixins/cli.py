from systems.command.parsers.config import ConfigTemplate
from utility.data import ensure_list


class CLITaskMixin(object):

    def _merge_options(self, options, overrides, lock = False):
        if not lock and overrides:
            return { **options, **overrides }
        return options

    def _interpolate(self, command, variables):
        final_command = []

        for component in ensure_list(command):
            parser = ConfigTemplate(component)
            try:
                final_command.append(parser.substitute(**variables))
            except KeyError as e:
                self.command.error("Configuration {} does not exist, escape literal with @@".format(e))

        return final_command
