from django.utils.timezone import now

from systems.models.index import Model, ModelFacade


class LogFacade(ModelFacade('log')):

    def get_field_message_render_display(self, instance, value, short):
        from systems.commands import messages

        display = []
        for record in instance.messages.all().order_by('created'):
            msg = messages.AppMessage.get(record.data, decrypt = False)
            display.append(msg.format(True))

        return "\n".join(display) + "\n"


class Log(Model('log')):

    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'


    def save(self, *args, **kwargs):
        if not self.name:
            self.name = "{}{}".format(
                now().strftime("%Y%m%d%H%M%S"),
                self.facade.generate_token(5)
            )
        super().save(*args, **kwargs)


    def success(self):
        return self.status == self.STATUS_SUCCESS

    def set_status(self, success):
        self.status = self.STATUS_SUCCESS if success else self.STATUS_FAILED


class LogMessage(Model('log_message')):

    def __str__(self):
        return "{} ({})".format(self.log.command, self.data)
