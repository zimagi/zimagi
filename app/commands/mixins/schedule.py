from datetime import datetime

from django.utils.timezone import make_aware

from systems.commands.index import CommandMixin

import re
import json
import string
import random


class ScheduleMixin(CommandMixin('schedule')):

    def get_schedule_from_representation(self, representation):
        schedule = self.get_interval_schedule(representation)

        if not schedule:
            schedule = self.get_datetime_schedule(representation)
        if not schedule:
            schedule = self.get_crontab_schedule(representation)

        if not schedule:
            self.error("'{}' is not a valid schedule format.  See --help for more information".format(representation))

        return schedule

    def normalize_schedule_time(self, time_string):
        return make_aware(datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S"))


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
                'task': 'zimagi.command.exec',
                'user': self.active_user,
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
        return "{}:{}{}".format(
            self.get_full_name().replace(' ', '-'),
            datetime.now().strftime("%Y%m%d%H%M%S"),
            random.SystemRandom().choice(string.ascii_lowercase)
        )


    def get_interval_schedule(self, representation):
        interval = self._task_interval.model
        schedule = None
        period_map = {
            'D': interval.DAYS,
            'H': interval.HOURS,
            'M': interval.MINUTES,
            'S': interval.SECONDS
        }

        match = re.match(r'^(\d+)([DHMS])$', representation, flags = re.IGNORECASE)
        if match:
            schedule, created = self._task_interval.store(representation,
                every = match.group(1),
                period = period_map[match.group(2).upper()],
            )
        return schedule

    def get_crontab_schedule(self, representation):
        schedule = None

        match = re.match(r'^([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+)$', representation)
        if match:
            schedule, created = self._task_crontab.store(representation,
                minute = match.group(1),
                hour = match.group(2),
                day_of_week = match.group(3),
                day_of_month = match.group(4),
                month_of_year = match.group(5)
            )
        return schedule

    def get_datetime_schedule(self, representation):
        schedule = None

        match = re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', representation)
        if match:
            schedule, created = self._task_datetime.store(representation,
                clocked_time = make_aware(datetime.strptime(representation, "%Y-%m-%d %H:%M:%S")),
            )
        return schedule
