from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import environment

from utility import terraform


class Command(
    environment.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'test'

    def exec(self):
        print('test')
