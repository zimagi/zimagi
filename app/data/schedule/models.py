from django_celery_beat import models as celery_beat_models

from systems.models.index import DerivedAbstractModel, Model, ModelFacade


class ScheduledTaskChanges(celery_beat_models.PeriodicTasks):

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
        celery_beat_models.ScheduledTaskChanges.update_changed()
        return result

    def clear(self, **filters):
        result = super().clear(**filters)
        celery_beat_models.ScheduledTaskChanges.update_changed()
        return result


class ScheduleModelMixin(object):

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        celery_beat_models.ScheduledTaskChanges.update_changed()


class TaskIntervalOverride(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'IntervalSchedule', id = None),
    Model('task_interval')
):
    pass

class TaskCrontabOverride(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'CrontabSchedule', id = None),
    Model('task_crontab')
):
    pass

class TaskDatetimeOverride(
    ScheduleModelMixin,
    DerivedAbstractModel(celery_beat_models, 'ClockedSchedule', id = None),
    Model('task_datetime')
):
    pass


class ScheduledTaskOverride(
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
    pass
