from celery import schedules
from django_celery_beat.clockedschedule import clocked
from django_celery_beat.schedulers import DatabaseScheduler, ModelEntry

from data.schedule.models import (
    ScheduledTaskChanges,
    ScheduledTask,
    TaskInterval,
    TaskCrontab,
    TaskDatetime
)
from utility.mutex import check_mutex, MutexError, MutexTimeoutError

import time
import random
import logging


logger = logging.getLogger(__name__)


class ScheduleEntry(ModelEntry):

    model_schedules = (
        (schedules.schedule, TaskInterval, 'interval'),
        (schedules.crontab, TaskCrontab, 'crontab'),
        (clocked, TaskDatetime, 'clocked')
    )

    @classmethod
    def from_entry(cls, name, app = None, **entry):
        return cls(ScheduledTask._default_manager.update_or_create(
            name = name, defaults = cls._unpack_fields(**entry),
        ), app = app)


class CeleryScheduler(DatabaseScheduler):

    Entry = ScheduleEntry
    Model = ScheduledTask
    Changes = ScheduledTaskChanges

    lock_id = 'zimagi-scheduler'


    def sync(self):
        try:
            time.sleep(random.randrange(10))
            with check_mutex(self.lock_id):
                super().sync()

        except MutexError:
            logger.warning("Scheduler could not obtain lock for {}".format(self.lock_id))

        except MutexTimeoutError:
            logger.warning("Scheduler sync completed but the lock timed out")
