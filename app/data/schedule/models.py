from django.core.exceptions import ValidationError
from django_celery_beat import models as celery_beat_models
from django_celery_beat import managers as celery_beat_managers

from systems.models.index import DerivedAbstractModel, Model, ModelFacade


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
            'celery.backend_cleanup',
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


class ScheduleModelMixin(object):

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ScheduledTaskChanges.update_changed()


class TaskInterval(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'IntervalSchedule', id = None),
    Model('task_interval')
):
    pass

class TaskCrontab(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'CrontabSchedule', id = None),
    Model('task_crontab')
):
    pass

class TaskDatetime(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'ClockedSchedule', id = None),
    Model('task_datetime')
):
    pass


class ScheduledTask(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'PeriodicTask',
        id = None,
        name = None,
        args = None,
        kwargs = None,
        interval = None,
        crontab = None,
        clocked = None,
        solar = None
    ),
    Model('scheduled_task')
):
    objects = celery_beat_managers.PeriodicTaskManager()

    def validate_unique(self, *args, **kwargs):
        super(celery_beat_models.PeriodicTask, self).validate_unique(*args, **kwargs)

        schedule_types = ['interval', 'crontab', 'clocked']
        selected_schedule_types = [s for s in schedule_types
                                   if getattr(self, s)]

        if len(selected_schedule_types) == 0:
            raise ValidationError(
                'One of clocked, interval, crontab, or solar '
                'must be set.'
            )

        err_msg = 'Only one of clocked, interval, crontab, '\
            'or solar must be set'
        if len(selected_schedule_types) > 1:
            error_info = {}
            for selected_schedule_type in selected_schedule_types:
                error_info[selected_schedule_type] = [err_msg]
            raise ValidationError(error_info)

        # clocked must be one off task
        if self.clocked and not self.one_off:
            err_msg = 'clocked must be one off, one_off must set True'
            raise ValidationError(err_msg)

    def save(self, *args, **kwargs):
        self.exchange = self.exchange or None
        self.routing_key = self.routing_key or None
        self.queue = self.queue or None
        self.headers = self.headers or None
        if not self.enabled:
            self.last_run_at = None
        self._clean_expires()
        self.validate_unique()
        super(celery_beat_models.PeriodicTask, self).save(*args, **kwargs)
