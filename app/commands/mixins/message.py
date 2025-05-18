import copy

from systems.commands.index import CommandMixin
from utility.data import clean_dict


class MessageMixin(CommandMixin("message")):
    def check_channel_permission(self):
        communication_spec = copy.deepcopy(self.manager.get_spec("channels", {}))

        if self.communication_channel not in communication_spec:
            self.error(f"Communication channel {self.communication_channel} does not exist")

        communication_spec = communication_spec[self.communication_channel]
        if not communication_spec:
            communication_spec = {}

        roles = list(clean_dict(communication_spec, False).keys())
        if not roles:
            return True

        return self.active_user.groups.filter(name__in=roles).exists()
