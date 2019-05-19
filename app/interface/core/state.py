from systems.command.factory import resource
from systems.command.types import state


class Command(state.StateRouterCommand):

    def get_subcommands(self):
        return resource.ResourceCommandSet(
            state.StateActionCommand, self.name,
            allow_update = False,
        )
