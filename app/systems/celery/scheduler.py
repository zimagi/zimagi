from celery import current_app, exceptions, schedules, beat
from django_celery_beat.clockedschedule import clocked
from django_celery_beat.schedulers import DatabaseScheduler, ModelEntry

from data.schedule.models import (
    ScheduledTaskChanges,
    ScheduledTask,
    TaskInterval,
    TaskCrontab,
    TaskDatetime
)
from utility.data import deep_merge

import sys
import copy
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
        obj, created = ScheduledTask._default_manager.update_or_create(
            name = name, defaults = cls._unpack_fields(**entry),
        )
        return cls(obj, app = app)

    @classmethod
    def _unpack_fields(cls, schedule,
        args = None,
        kwargs = None,
        relative = None,
        options = None,
        **entry
    ):
        entry_schedules = {
            model_field: None for _, _, model_field in cls.model_schedules
        }
        model_schedule, model_field = cls.to_model_schedule(schedule)
        entry_schedules[model_field] = model_schedule
        entry.update(
            entry_schedules,
            args = args or [],
            kwargs = kwargs or {},
            **cls._unpack_options(**options or {})
        )
        return entry

    @classmethod
    def _unpack_options(cls,
        queue = None,
        exchange = None,
        routing_key = None,
        priority = None,
        headers = None,
        expire_seconds = None,
        **kwargs
    ):
        return {
            'queue': queue,
            'exchange': exchange,
            'routing_key': routing_key,
            'priority': priority,
            'headers': headers or {},
            'expire_seconds': expire_seconds,
        }


    def __init__(self, model, app = None):
        self.app = app or current_app._get_current_object()
        self.name = model.name
        self.task = model.task
        try:
            self.schedule = model.schedule
        except model.DoesNotExist:
            logger.error(
                'Disabling schedule %s that was removed from database',
                self.name,
            )
            self._disable(model)

        self.args = model.args
        self.kwargs = model.kwargs
        self.secrets = model.secrets

        self.options = {}
        for option in ['queue', 'exchange', 'routing_key', 'priority']:
            value = getattr(model, option)
            if value is not None:
                self.options[option] = value

        if getattr(model, 'expires_', None):
            self.options['expires'] = getattr(model, 'expires_')

        self.options['headers'] = model.headers or {}
        self.options['periodic_task_name'] = model.name

        self.total_run_count = model.total_run_count
        self.model = model

        if not model.last_run_at:
            model.last_run_at = self._default_now()

        self.last_run_at = model.last_run_at


class CeleryScheduler(DatabaseScheduler):

    Entry = ScheduleEntry
    Model = ScheduledTask
    Changes = ScheduledTaskChanges


    def install_default_entries(self, data):
        self.update_from_dict({})


    def apply_async(self, entry, producer = None, advance = True, **kwargs):
        entry = self.reserve(entry) if advance else entry
        task = self.app.tasks.get(entry.task)

        options = copy.deepcopy(entry.options)
        options['queue'] = entry.kwargs.get('worker_type', 'default')
        try:
            entry_args = beat._evaluate_entry_args(entry.args)
            entry_kwargs = beat._evaluate_entry_kwargs(
                deep_merge(entry.kwargs, entry.secrets, merge_lists = True, merge_null = False)
            )
            if task:
                return task.apply_async(entry_args, entry_kwargs,
                                        producer = producer,
                                        **options)
            else:
                return self.send_task(entry.task, entry_args, entry_kwargs,
                                      producer = producer,
                                      **options)
        except Exception as exc:
            exceptions.reraise(beat.SchedulingError, beat.SchedulingError(
                "Couldn't apply scheduled task {0.name}: {exc}".format(
                    entry, exc = exc)), sys.exc_info()[2])
        finally:
            self._tasks_since_sync += 1
            if self.should_sync():
                self._do_sync()
