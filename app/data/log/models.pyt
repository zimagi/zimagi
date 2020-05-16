from django.db import models as django
from django.utils.timezone import now

from data.mixins import config
from data.user.models import User
from data.environment import models as environment
from systems.models import fields


class LogFacade(
    config.ConfigModelFacadeMixin,
    environment.EnvironmentBaseFacadeMixin
):
    def get_packages(self):
        return [] # Do not export with db dumps!!


    def get_field_user_display(self, instance, value, short):
        return self.relation_color(str(value))

    def get_field_messages_display(self, instance, value, short):
        from systems.command import messages

        display = []
        for record in instance.messages.all():
            msg = messages.AppMessage.get(record.data, decrypt = False)
            display.append(msg.format(True))

        return "\n".join(display) + "\n"


class Log(
    config.ConfigMixin,
    environment.EnvironmentBase
):
    user = django.ForeignKey(User, null = True, on_delete = django.PROTECT, related_name = '+')
    command = django.CharField(max_length = 256, null = True)
    status = django.CharField(max_length = 64, null = True)

    scheduled = django.BooleanField(default = False)
    task_id = django.CharField(null = True, max_length = 256)

    class Meta(environment.EnvironmentBase.Meta):
        verbose_name = "log"
        verbose_name_plural = "logs"
        facade_class = LogFacade
        ordering = ['-created']
        dynamic_fields = ['messages']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.STATUS_SUCCESS = 'success'
        self.STATUS_FAILED = 'failed'

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


class LogMessage(django.Model):
    log = django.ForeignKey(Log, related_name='messages', on_delete=django.CASCADE)
    data = fields.EncryptedDataField(null = True)

    class Meta:
        db_table = 'core_log_messages'

    def __str__(self):
        return "{} ({})".format(self.log.command, self.data)
