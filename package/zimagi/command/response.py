
class CommandResponse(object):

    def __init__(self):
        self.messages = []
        self.named = {}
        self.errors = []


    def __getitem__(self, name):
        return self.get_named_data(name)


    @property
    def active_user(self):
        return self.get_named_data('active_user')

    @property
    def log_key(self):
        return self.get_named_data('log_key')


    def add(self, messages):
        if not isinstance(messages, (list, tuple)):
            messages = [messages]

        for message in messages:
            self.messages.append(message)
            if message.name:
                self.named[message.name] = message
            if message.is_error():
                self.errors.append(message)


    @property
    def aborted(self):
        return len(self.errors) > 0

    @property
    def error(self):
        return self.aborted


    def error_message(self):
        messages = []
        for message in self.errors:
            messages.append(message.format())

        return "\n\n".join(messages)


    def get_named_data(self, name):
        message = self.named.get(name, None)
        if message:
            try:
                return message.data
            except AttributeError:
                return message.message
        return None
