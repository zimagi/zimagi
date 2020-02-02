from django.db import models as django
from django_celery_beat.models import (
    PeriodicTask,
    PeriodicTasks,
    IntervalSchedule,
    CrontabSchedule,
    ClockedSchedule
)

from systems.models import fields, environment

import json


class ScheduledTaskChanges(PeriodicTasks):

    class Meta:
        verbose_name = "scheduled task change"
        verbose_name_plural = "scheduled task changes"
        db_table = 'core_task_changes'


class ScheduledIntervalFacade(
    environment.EnvironmentModelFacadeMixin
):
    pass

class ScheduledTaskFacade(
    environment.EnvironmentModelFacadeMixin
):
    def keep(self):
        return [
            'celery.backend_cleanup',
            'clean_interval_schedules',
            'clean_crontab_schedules',
            'clean_datetime_schedules'
        ]


    def get_field_args_display(self, instance, value, short):
        value = json.loads(value)
        if isinstance(value, (list, tuple)):
            value = " ".join(value)
        return self.encrypted_color(value)

    def get_field_kwargs_display(self, instance, value, short):
        value = json.loads(value)
        if isinstance(value, dict):
            lines = []
            for key, val in value.items():
                lines.append("{} = {}".format(key, val))
            value = "\n".join(lines)
        return self.encrypted_color(value)


class ScheduleModelMixin(object):

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ScheduledTaskChanges.update_changed()


class TaskInterval(
    IntervalSchedule,
    ScheduleModelMixin,
    environment.EnvironmentModel
):
    class Meta:
        verbose_name = "task interval"
        verbose_name_plural = "task intervals"
        facade_class = ScheduledIntervalFacade


class TaskCrontab(
    CrontabSchedule,
    ScheduleModelMixin,
    environment.EnvironmentModel
):
    class Meta:
        verbose_name = "task crontab"
        verbose_name_plural = "task crontabs"
        facade_class = ScheduledIntervalFacade


class TaskDatetime(
    ClockedSchedule,
    ScheduleModelMixin,
    environment.EnvironmentModel
):
    class Meta:
        verbose_name = "task datetime"
        verbose_name_plural = "task datetimes"
        facade_class = ScheduledIntervalFacade


class ScheduledTask(
    PeriodicTask,
    ScheduleModelMixin,
    environment.EnvironmentModel
):
    name = django.CharField(max_length = 256, editable = False)
    args = fields.EncryptedDataField(default = "[]")
    kwargs = fields.EncryptedDataField(default = "{}")

    interval = django.ForeignKey(TaskInterval,
        on_delete = django.CASCADE,
        null = True, blank = True,
        editable = False
    )
    crontab = django.ForeignKey(TaskCrontab,
        on_delete = django.CASCADE,
        null = True, blank = True,
        editable = False
    )
    solar = None
    clocked = django.ForeignKey(TaskDatetime,
        on_delete = django.CASCADE,
        null = True, blank = True,
        editable = False
    )

    class Meta:
        verbose_name = "scheduled task"
        verbose_name_plural = "scheduled tasks"
        facade_class = ScheduledTaskFacade
        command_base = 'schedule'
