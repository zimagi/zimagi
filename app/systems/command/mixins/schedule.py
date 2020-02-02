from datetime import datetime

from django.conf import settings
from django.utils.timezone import make_aware

from .base import DataMixin
from data.schedule.models import (
    ScheduledTask,
    TaskInterval,
    TaskCrontab,
    TaskDatetime
)

import re
import json
import string
import random


class ScheduleMixin(DataMixin):

    schema = {
        'scheduled_task': {
            'model': ScheduledTask
        },
        'interval': {
            'model': TaskInterval
        },
        'crontab': {
            'model': TaskCrontab
        },
        'clocked': {
            'model': TaskDatetime
        }
    }

    def parse_schedule(self, optional = '--schedule', help_text = "schedule in the form of timedelta '#D | #H | #M | #S',\ncrontab 'M H Dm My Dw', or datetime 'YYYY-MM-DD HH:MM:SS'"):
        self.parse_variable('schedule', optional, str, help_text,
            value_label = "SCHEDULE (timedelta | crontab | datetime) - TZ: {}".format(settings.TIME_ZONE),
        )

    @property
    def schedule(self):
        representation = self.options.get('schedule', None)

        if representation:
            schedule = self.get_interval_schedule(representation)

            if not schedule:
                schedule = self.get_datetime_schedule(representation)
            if not schedule:
                schedule = self.get_crontab_schedule(representation)

            if not schedule:
                self.error("'{}' is not a valid schedule format.  See --help for more information".format(representation))

            return schedule

        return None


    def parse_schedule_begin(self, optional = '--begin', help_text = 'date to begin processing in form of "YYYY-MM-DD HH:MM:SS"'):
        self.parse_variable('schedule_begin', optional, str, help_text,
            value_label = "DATE/TIME (YYYY-MM-DD HH:MM:SS) - TZ: {}".format(settings.TIME_ZONE),
        )

    @property
    def schedule_begin(self):
        begin = self.options.get('schedule_begin', None)
        if begin:
            begin = make_aware(datetime.strptime(begin, "%Y-%m-%d %H:%M:%S"))
        return begin

    def parse_schedule_end(self, optional = '--end', help_text = 'date to end processing in form of "YYYY-MM-DD HH:MM:SS"'):
        self.parse_variable('schedule_end', optional, str, help_text,
            value_label = "DATE/TIME (YYYY-MM-DD HH:MM:SS) - TZ: {}".format(settings.TIME_ZONE),
        )

    @property
    def schedule_end(self):
        end = self.options.get('schedule_end', None)
        if end:
            end = make_aware(datetime.strptime(end, "%Y-%m-%d %H:%M:%S"))
        return end


    def parse_notify(self, optional = '--notify', help_text = 'user group names to notify of results when scheduled'):
        self.parse_variables('notify', optional, str, help_text,
            value_label = 'GROUP_NAME'
        )

    @property
    def notify(self):
        return self.options.get('notify', [])


    def set_periodic_task(self):
        schedule = self.schedule

        if schedule:
            begin = self.schedule_begin
            end = self.schedule_end

            schedule_map = {
                'task_interval': 'interval',
                'task_crontab': 'crontab',
                'task_datetime': 'clocked'
            }
            options = self.options.export()
            options['_user'] = self.active_user.name
            task = {
                schedule_map[schedule.facade.name]: schedule,
                'task': 'mcmi.command.exec',
                'args': json.dumps([self.get_full_name()]),
                'kwargs': json.dumps(options)
            }
            if begin:
                task['start_time'] = begin
            if end:
                task['expires'] = end

            self._scheduled_task.store(self.get_schedule_name(), **task)

            self.success("Task '{}' has been scheduled to execute periodically".format(self.get_full_name()))
            return True

        return False


    def get_schedule_name(self):
        chars = string.ascii_lowercase + string.digits
        random_text = ''.join(random.SystemRandom().choice(chars) for _ in range(5))
        return "{}-{}-{}".format(self.get_full_name(), datetime.now().strftime("%Y%m%d%H%M%S"), random_text)


    def get_interval_schedule(self, representation):
        schedule = None
        period_map = {
            'D': TaskInterval.DAYS,
            'H': TaskInterval.HOURS,
            'M': TaskInterval.MINUTES,
            'S': TaskInterval.SECONDS
        }

        if match := re.match(r'^(\d+)([DHMS])$', representation, flags=re.IGNORECASE):
            schedule, created = self._interval.store(representation,
                every = match.group(1),
                period = period_map[match.group(2).upper()],
            )
        return schedule

    def get_crontab_schedule(self, representation):
        schedule = None

        if match := re.match(r'^([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+)$', representation):
            schedule, created = self._crontab.store(representation,
                minute = match.group(1),
                hour = match.group(2),
                day_of_week = match.group(3),
                day_of_month = match.group(4),
                month_of_year = match.group(5)
            )
        return schedule

    def get_datetime_schedule(self, representation):
        schedule = None

        if match := re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', representation):
            schedule, created = self._clocked.store(representation,
                clocked_time = make_aware(datetime.strptime(representation, "%Y-%m-%d %H:%M:%S")),
            )
        return schedule
