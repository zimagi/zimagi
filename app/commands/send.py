from systems.commands.index import Command
from systems.manage.task import channel_communication_key
from utility.data import normalize_value, dump_json
from utility.time import Time


class Send(Command('send')):

    def exec(self):
        connection = self.manager.task_connection()
        if connection:
            data = {
                'user': self.active_user.name,
                'time': Time().now_string,
                'message': normalize_value(self.communication_message, parse_json = True)
            }
            connection.publish(
                channel_communication_key(self.communication_channel),
                dump_json(data, indent = 2)
            )
        self.success("Message sent to channel {}: {}".format(self.communication_channel, self.communication_message))
