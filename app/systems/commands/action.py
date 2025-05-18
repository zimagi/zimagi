import logging

from django.conf import settings
from systems.commands import exec

logger = logging.getLogger(__name__)


def primary(name, options=None, user=None, log=False, interpolate=True):
    command = ActionCommand(name, settings.MANAGER.active_command)
    command.set_option_defaults(interpolate=interpolate)

    if user:
        if isinstance(user, str):
            user = command._user.retrieve(user)
        command._user.set_active_user(user)

    if options:
        command.set_options(options, custom=True, clear=False)
    if log:
        command.log_init()

    return command


def child(parent, name, options=None, log=True, interpolate=True):
    command = ActionCommand(name, parent)
    command.set_option_defaults(interpolate=interpolate)

    if options:
        command.set_options(options, custom=True, clear=False)
    if log:
        command.log_init()

    return command


class ActionCommand(exec.ExecCommand):

    def parse_base(self, addons=None, add_api_fields=False):
        def action_addons():
            if self.require_db() and self.api_enabled():
                # Scheduling
                self.parse_schedule()
                self.parse_schedule_begin()
                self.parse_schedule_end()

            if callable(addons):
                addons()

        super().parse_base(action_addons, add_api_fields)

    def _exec_local_handler(self, log_key, primary=True):
        profiler_name = "exec.action.local.primary" if primary else "exec.action.local"
        notify = False

        if not self.set_periodic_task() and ((primary and settings.WORKER_EXEC) or not self.set_queue_task(log_key)):
            try:
                self.start_profiler(profiler_name)
                self.run_exclusive(
                    self.lock_id,
                    self.exec,
                    error_on_locked=self.lock_error,
                    timeout=self.lock_timeout,
                    interval=self.lock_interval,
                    run_once=self.run_once,
                )
            finally:
                self.stop_profiler(profiler_name)

            notify = True

        return notify

    def _exec_api_handler(self, log_key):
        profiler_name = "exec.action.api"
        notify = False

        if not self.set_periodic_task() and not self.set_queue_task(log_key):
            try:
                self.start_profiler(profiler_name)
                self.run_exclusive(
                    self.lock_id,
                    self.exec,
                    error_on_locked=self.lock_error,
                    timeout=self.lock_timeout,
                    interval=self.lock_interval,
                    run_once=self.run_once,
                )
            finally:
                self.stop_profiler(profiler_name)

            notify = True
        return notify
