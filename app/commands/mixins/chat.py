import sys

from contextlib import contextmanager
from django.conf import settings

from systems.commands.index import CommandMixin


class ChatMixin(CommandMixin("chat")):

    def exec_chat(self):
        if settings.CLI_EXEC:
            for response in self._chat_loop():
                self.process_response(response)

        elif settings.WSGI_EXEC or settings.WORKER_EXEC:
            self.respond()

    def get_chat_prompt(self):
        return "> "

    def respond(self):
        raise NotImplementedError("Method 'respond' must be implemented in chat commands")

    def process_response(self, response):
        # Override in command if needed
        pass

    def _chat_loop(self):
        while True:
            user_input_message = self._get_user_input()
            yield self._send_message(user_input_message)

    def _get_chat(self):
        chat = self._chat.filter(name=self.chat_name, user=self.active_user).first()
        if not chat:
            (chat, created) = self._chat.store(None, {"name": self.chat_name, "user": self.active_user})
        return chat

    def _get_chat_messages(self, chat):
        if self.chat_clear:
            self._chat_message.clear(chat=chat)

        self._chat_message.store(
            None, {"chat": chat, "role": self._chat_message.model.ROLE_USER, "content": self.user_chat_message}
        )
        return list(self._chat_message.set_order("created").values("role", "content", chat=chat))

    @contextmanager
    def _record_chat_message(self, chat):
        content = []

        self.start_capture()
        yield

        for message in self.get_captured_messages():
            content.append(message.format(disable_color=True))

        self._chat_message.store(
            None, {"chat": chat, "role": self._chat_message.model.ROLE_ASSISTANT, "content": "\n".join(content)}
        )

    def _get_user_input(self):
        if not settings.CLI_EXEC:
            self.error("User input can not be accepted in API mode")

        sys.stdout.write(self.get_chat_prompt())
        user_input_message = self._fetch_lines()

        if user_input_message.upper() == "EXIT":
            self.error("User exited", "abort")

        return user_input_message

    def _fetch_lines(self):
        input_lines = []

        while True:
            input_line = input()
            input_lines.append(input_line)

            if not input_line or input_line.upper() == "EXIT":
                break

            sys.stdout.write("\n")

        return "\n\n".join(input_lines).strip()

    def _send_message(self, message):
        host = self.get_host()
        if host:
            return self.exec_remote(
                host,
                self.get_full_name(),
                {"chat_name": self.chat_name, "chat_clear": self.chat_clear, "user_chat_message": message},
                include_system_messages=False,
            )
