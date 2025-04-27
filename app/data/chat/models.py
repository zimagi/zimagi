from systems.models.index import Model, ModelFacade


class ChatFacade(ModelFacade("chat")):
    def get_field_message_render_display(self, instance, value, short):
        display = []
        for record in instance.messages.all().order_by("created"):
            display.append(record.content)

        return "\n".join(display) + "\n"


class Chat(Model("chat")):
    pass


class ChatMessage(Model("chat_message")):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    def __str__(self):
        return self.content
