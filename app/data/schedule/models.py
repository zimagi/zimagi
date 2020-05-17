from django_celery_beat.models import (
    PeriodicTask,
    PeriodicTasks,
    IntervalSchedule,
    CrontabSchedule,
    ClockedSchedule
)

from systems.models.index import Model, ModelFacade


class ScheduledTaskChanges(PeriodicTasks):

    class Meta:
        verbose_name = "scheduled task change"
        verbose_name_plural = "scheduled task changes"
        db_table = 'core_task_changes'


class ScheduledTaskFacadeOverride(ModelFacade('scheduled_task')):

    def keep(self):
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


class TaskIntervalOverride(
    IntervalSchedule,
    ScheduleModelMixin,
    Model('task_interval')
):
    pass

class TaskCrontabOverride(
    CrontabSchedule,
    ScheduleModelMixin,
    Model('task_crontab')
):
    pass

class TaskDatetimeOverride(
    ClockedSchedule,
    ScheduleModelMixin,
    Model('task_datetime')
):
    pass


class ScheduledTaskOverride(
    PeriodicTask,
    ScheduleModelMixin,
    Model('scheduled_task')
):
    pass
