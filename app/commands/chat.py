from django.conf import settings
from systems.commands.index import Command


class Chat(Command("chat")):

    def exec(self):
        self.exec_chat()

    def respond(self):
        self.send(
            "core:chat:request", {"user": self.active_user.name, "name": self.chat_name, "message": self.user_chat_message}
        )
        for package in self.listen("core:chat:response", state_key="core_chat_command", timeout=120, block_sec=1):
            message = package.message
