from systems.commands.index import Command
from systems.manage.communication import channel_communication_key
from utility.data import dump_json, normalize_value
from utility.time import Time


class Send(Command("send")):
    def exec(self):
        if not self.check_channel_permission():
            self.error(f"You do not have permission to access the {self.communication_channel} channel")

        connection = self.manager.communication_connection()
        if connection:
            data = {
                "user": self.active_user.name,
                "time": Time().now_string,
                "message": normalize_value(self.communication_message, parse_json=True),
            }
            connection.publish(channel_communication_key(self.communication_channel), dump_json(data, indent=2))
        self.success(f"Message sent to channel {self.communication_channel}: {self.communication_message}")
