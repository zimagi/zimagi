import copy
import random
import re
import string
from datetime import datetime

from django.utils.timezone import make_aware
from kombu.exceptions import OperationalError
from settings.tasks import exec_command
from systems.commands.index import CommandMixin


class ScheduleMixin(CommandMixin("schedule")):
    def get_schedule_from_representation(self, representation):
        schedule = self.get_interval_schedule(representation)

        if not schedule:
            schedule = self.get_datetime_schedule(representation)
        if not schedule:
            schedule = self.get_crontab_schedule(representation)

        if not schedule:
            self.error(f"'{representation}' is not a valid schedule format.  See --help for more information")

        return schedule

    def normalize_schedule_time(self, time_string):
        return make_aware(datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S"))

    def set_periodic_task(self):
        schedule = self.schedule

        if self.require_db() and schedule:
            schedule_name = self.get_schedule_name()
            begin = self.schedule_begin
            end = self.schedule_end

            schedule_map = {"task_interval": "interval", "task_crontab": "crontab", "task_datetime": "clocked"}
            schedule_options = {"_user": self.active_user.name, "_schedule": schedule_name}
            task = {
                schedule_map[schedule.facade.name]: schedule,
                "task": "zimagi.command.exec",
                "user": self.active_user,
                "args": [self.get_full_name()],
                "kwargs": {**schedule_options, **self.options.export()},
            }
            if begin:
                task["start_time"] = begin
            if end:
                task["expires"] = end

            self._scheduled_task.store(schedule_name, task, command=self)

            self.success(f"Task '{self.get_full_name()}' has been scheduled to execute periodically")
            return True

        return False

    def set_queue_task(self, log_key, background=False):
        def follow_progress(verbosity):
            def follow(data):
                self.message(self.create_message(data, decrypt=False), verbosity=verbosity, log=False)

            self.manager.follow_task(log_key, follow)
            if self.log_entry.failed():
                self.error("", silent=True)
            return True

        if (self.background_process or background) and self.require_db() and self.worker_type != "none":
            options = self.options.export()
            options["_user"] = self.active_user.name
            options["_log_key"] = log_key

            try:
                copy.deepcopy(exec_command).apply_async(
                    args=[self.get_full_name()], kwargs=options, queue=self.worker_type, priority=self.worker_task_priority
                )
            except OperationalError as error:
                self.error(f"Connection to scheduling queue could not be made.  Check service and try again: {error}")

            if not self.async_exec:
                return follow_progress(options.get("verbosity", None))

            self.success(
                f"Task '{self.get_full_name()}' has been pushed to the queue to execute in the background: {options}"
            )
            return True
        return False

    def wait_for_tasks(self, log_keys):
        self.manager.wait_for_tasks(log_keys)

    def publish_message(self, data, include=True):
        def _publish_message(command, data, _include):
            if getattr(command, "log_entry", None) and _include:
                self.manager.publish_task_message(command.log_entry.name, data)

            if command.exec_parent:
                _publish_message(command.exec_parent, data, True)

        _publish_message(self, data, include)

    def publish_exit(self):
        if self.log_result and getattr(self, "log_entry", None):
            self.manager.publish_task_exit(self.log_entry.name)

    def check_abort(self):
        if self.log_result and getattr(self, "log_entry", None):
            return self.manager.check_task_abort(self.log_entry.name)
        return None

    def publish_abort(self, log_key):
        if self.log_result:
            self.manager.publish_task_abort(log_key)

    def get_schedule_name(self):
        return "{}_{}{}".format(
            self.get_full_name().replace(" ", "-"),
            datetime.now().strftime("%Y%m%d%H%M%S"),
            random.SystemRandom().choice(string.ascii_lowercase),
        )

    def get_interval_schedule(self, representation):
        interval = self._task_interval.model
        schedule = None
        period_map = {"D": interval.DAYS, "H": interval.HOURS, "M": interval.MINUTES, "S": interval.SECONDS}

        match = re.match(r"^(\d+)([DHMS])$", representation, flags=re.IGNORECASE)
        if match:
            schedule, created = self._task_interval.store(
                representation,
                {
                    "every": match.group(1),
                    "period": period_map[match.group(2).upper()],
                },
                command=self,
            )
        return schedule

    def get_crontab_schedule(self, representation):
        schedule = None

        match = re.match(
            r"^([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+) ([\*\d\-\/\,]+)$", representation
        )
        if match:
            schedule, created = self._task_crontab.store(
                representation,
                {
                    "minute": match.group(1),
                    "hour": match.group(2),
                    "day_of_week": match.group(3),
                    "day_of_month": match.group(4),
                    "month_of_year": match.group(5),
                },
                command=self,
            )
        return schedule

    def get_datetime_schedule(self, representation):
        schedule = None

        match = re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", representation)
        if match:
            schedule, created = self._task_datetime.store(
                representation,
                {"clocked_time": make_aware(datetime.strptime(representation, "%Y-%m-%dT%H:%M:%S"))},
                command=self,
            )
        return schedule
