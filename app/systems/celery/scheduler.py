from celery import schedules
from django_celery_beat.clockedschedule import clocked
from django_celery_beat.schedulers import DatabaseScheduler, ModelEntry

from db_mutex import DBMutexError, DBMutexTimeoutError
from db_mutex.models import DBMutex
from db_mutex.db_mutex import db_mutex

from data.schedule.models import (
    ScheduledTaskChanges,
    ScheduledTask,
    TaskInterval,
    TaskCrontab,
    TaskDatetime
)

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
            with db_mutex(self.lock_id):
                super().sync()

        except DBMutexError:
            logger.warning("Scheduler could not obtain lock for {}".format(self.lock_id))

        except DBMutexTimeoutError:
            logger.warning("Scheduler sync completed but the lock timed out")

        except Exception as e:
            DBMutex.objects.filter(lock_id = self.lock_id).delete()
            raise e
