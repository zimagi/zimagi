import time

from systems.commands.index import Command
from systems.manage.communication import channel_communication_key
from utility.data import normalize_value
from utility.time import Time


class Listen(Command("listen")):
    def exec(self):
        if not self.check_channel_permission():
            self.error(f"You do not have permission to access the {self.communication_channel} channel")

        connection = self.manager.communication_connection()
        if connection:
            subscription = connection.pubsub(ignore_subscribe_messages=True)
            try:
                subscription.subscribe(channel_communication_key(self.communication_channel))

                start_time = time.time()
                current_time = start_time

                self.data("Listening for messages on channel", self.communication_channel)
                self.spacing()
                while not self.disconnected:
                    message = subscription.get_message()
                    if message:
                        if message["type"] == "message":
                            self.data(Time().now_string, normalize_value(message["data"], parse_json=True), "message")
                            start_time = time.time()

                    self.sleep(0.25)
                    current_time = time.time()

                    if self.communication_timeout and ((current_time - start_time) > self.communication_timeout):
                        self.error(f"Listener timed out without any messages after {self.communication_timeout} seconds")
            finally:
                subscription.close()
