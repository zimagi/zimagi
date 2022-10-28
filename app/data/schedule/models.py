from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django_celery_beat import models as celery_beat_models
from django_celery_beat import querysets as celery_beat_querysets

from systems.models.index import DerivedAbstractModel, Model, ModelFacade
from utility.data import load_json

import yaml


class ScheduledTaskChanges(celery_beat_models.PeriodicTasks):

    class Meta:
        verbose_name = "scheduled task change"
        verbose_name_plural = "scheduled task changes"
        db_table = 'core_task_changes'


class ScheduledTaskFacade(ModelFacade('scheduled_task')):

    def keep(self, key = None):
        if key:
            return []

        return [
            'clean_interval_schedules',
            'clean_crontab_schedules',
            'clean_datetime_schedules'
        ]


    def delete(self, key, **filters):
        result = super().delete(key, **filters)
        ScheduledTaskChanges.update_changed()
        return result

    def clear(self, **filters):
        result = super().clear(**filters)
        ScheduledTaskChanges.update_changed()
        return result


    def get_field_args_display(self, instance, value, short):
        return super().get_field_args_display(
            instance,
            yaml.dump(value),
            short
        )

    def get_field_kwargs_display(self, instance, value, short):
        return super().get_field_kwargs_display(
            instance,
            yaml.dump(value),
            short
        )


class ScheduleModelMixin(object):

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ScheduledTaskChanges.update_changed()


class TaskInterval(
    ScheduleModelMixin,
    Model('task_interval'),
    DerivedAbstractModel(celery_beat_models, 'IntervalSchedule', 'id')
):
    pass

class TaskCrontab(
    ScheduleModelMixin,
    Model('task_crontab'),
    DerivedAbstractModel(celery_beat_models, 'CrontabSchedule', 'id')
):
    pass

class TaskDatetime(
    ScheduleModelMixin,
    Model('task_datetime'),
    DerivedAbstractModel(celery_beat_models, 'ClockedSchedule', 'id')
):
    pass


class ScheduledTask(
    Model('scheduled_task'),
    DerivedAbstractModel(celery_beat_models, 'PeriodicTask',
        'id',
        'name',
        'args',
        'kwargs',
        'headers',
        'interval',
        'crontab',
        'clocked',
        'solar'
    )
):
    objects = celery_beat_querysets.PeriodicTaskQuerySet.as_manager()


    def validate_unique(self, *args, **kwargs):
        super(celery_beat_models.PeriodicTask, self).validate_unique(*args, **kwargs)

        schedule_types = ['interval', 'crontab', 'clocked']
        selected_schedule_types = [
            schedule_type for schedule_type in schedule_types if getattr(self, schedule_type)
        ]

        if len(selected_schedule_types) == 0:
            raise ValidationError('One of clocked, interval, or crontab must be set.')

        if len(selected_schedule_types) > 1:
            error_info = {}
            for selected_schedule_type in selected_schedule_types:
                error_info[selected_schedule_type] = [
                    'Only one of clocked, interval, or crontab must be set'
                ]
            raise ValidationError(error_info)


    def save(self, *args, **kwargs):
        self.exchange = self.exchange or None
        self.routing_key = self.routing_key or None
        self.queue = self.queue or None
        self.headers = self.headers or {}

        if self.created is None:
            self.created = now()
        self.updated = now()

        if self.clocked:
            self.one_off = True
        if not self.enabled:
            self.last_run_at = None

        self._clean_expires()
        self.validate_unique()

        super(celery_beat_models.PeriodicTask, self).save(*args, **kwargs)
        ScheduledTaskChanges.changed(self)


    def delete(self, *args, **kwargs):
        super(celery_beat_models.PeriodicTask, self).delete(*args, **kwargs)
        ScheduledTaskChanges.changed(self)
