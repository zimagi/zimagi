from django.conf import settings
from django.db import connection
from django.core.management.base import CommandError

from systems.command import base, args, messages, registry
from systems.command.mixins import command, log, schedule, notification
from systems.api import client
from utility.runtime import Runtime
from utility import display

import threading
import time
import logging
import copy
import yaml


logger = logging.getLogger(__name__)


class ActionResult(object):

    def __init__(self):
        self.stream = []
        self.named = {}
        self.errors = []


    @property
    def active_user(self):
        return self.get_named_data('active_user')


    def add(self, messages):
        if not isinstance(messages, (list, tuple)):
            messages = [messages]

        for msg in messages:
            self.stream.append(msg)
            if msg.name:
                self.named[msg.name] = msg
            if msg.type == 'ErrorMessage':
                self.errors.append(msg)


    @property
    def aborted(self):
        return len(self.errors) > 0

    def error_message(self):
        messages = []
        for msg in self.errors:
            messages.append(msg.format())

        return "\n".join(messages)


    def get_named_data(self, name):
        msg = self.named.get(name, None)
        if msg:
            return msg.data
        return None


class ActionCommand(
    command.ExecMixin,
    log.LogMixin,
    schedule.ScheduleMixin,
    notification.NotificationMixin,
    base.AppBaseCommand
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disconnected = False
        self.log_result = True
        self.notification_messages = []


    def queue(self, msg):
        data = super().queue(msg)
        if self.log_result:
            self.log_message(data)

        self.notification_messages.append(
            self.raw_text(msg.format(disable_color = True))
        )
        return data


    def get_action_result(self):
        return ActionResult()

    def display_header(self):
        return True


    def parse_base(self):
        super().parse_base()

        if not self.parse_passthrough():
            self.parse_lock_id()
            self.parse_lock_error()
            self.parse_lock_no_wait()
            self.parse_lock_timeout()
            self.parse_lock_interval()

            if not settings.API_EXEC:
                self.parse_local()
                self.parse_reverse_status()

            if self.server_enabled():
                self.parse_schedule()
                self.parse_schedule_begin()
                self.parse_schedule_end()
                self.parse_command_notify()
                self.parse_command_notify_failure()


    def parse_local(self):
        self.parse_flag('local', '--local', "force command to run in local environment")

    @property
    def local(self):
        return self.options.get('local', False)

    def parse_reverse_status(self):
        self.parse_flag('reverse_status', '--reverse-status', "reverse exit status of command (error on success)")

    @property
    def reverse_status(self):
        return self.options.get('reverse_status', False)


    def parse_lock_id(self):
        self.parse_variable('lock_id', '--lock', str,
            'command lock id to prevent simultanious duplicate execution',
            value_label = 'UNIQUE_NAME',
        )

    @property
    def lock_id(self):
        return self.options.get('lock_id', None)

    def parse_lock_error(self):
        self.parse_flag('lock_error', '--lock-error', 'raise an error and abort if commmand lock can not be established')

    @property
    def lock_error(self):
        return self.options.get('lock_error', False)

    def parse_lock_no_wait(self):
        self.parse_flag('lock_no_wait', '--lock-no-wait', 'return immediately if command lock can not be established')

    @property
    def lock_no_wait(self):
        return self.options.get('lock_no_wait', False)

    def parse_lock_timeout(self):
        self.parse_variable('lock_timeout', '--lock-timeout', int,
            'command lock wait timeout in seconds',
            value_label = 'SECONDS',
            default = 600
        )

    @property
    def lock_timeout(self):
        return self.options.get('lock_timeout', 600)

    def parse_lock_interval(self):
        self.parse_variable('lock_interval', '--lock-interval', int,
            'command lock check interval in seconds',
            value_label = 'SECONDS',
            default = 2
        )

    @property
    def lock_interval(self):
        return self.options.get('lock_interval', 2)


    def confirm(self):
        # Override in subclass
        pass

    def _exec_wrapper(self):
        width = Runtime.width()
        try:
            success = True

            if self.display_header() and self.verbosity > 1:
                user_label = "> active user"
                user_info_width = len(user_label) + len(self.active_user.name) + 4

                self.info("-" * user_info_width)
                self.data(user_label, self.active_user.name, 'active_user')
                self.info("-" * user_info_width)

            if not self.set_periodic_task():
                self.run_exclusive(self.lock_id, self.exec,
                    error_on_locked = self.lock_error,
                    wait = not self.lock_no_wait,
                    timeout = self.lock_timeout,
                    interval = self.lock_interval
                )

        except Exception as e:
            success = False

            if not isinstance(e, CommandError):
                self.error(e,
                    terminate = False,
                    traceback = display.format_exception_info()
                )
        finally:
            if self.log_result:
                self.log_status(success)

            self.send_notifications(success)
            self.flush()
            #connection.close()


    def exec(self):
        # Override in subclass
        pass

    def exec_local(self, name, options = None, task = None):
        if not options:
            options = {}

        command = self.registry.find_command(name, self)
        command.mute = self.mute

        options = command.format_fields(
            copy.deepcopy(options)
        )
        command.bootstrap(options)
        command.options.add('local', not self.server_enabled() or self.local, False)
        command.handle(options, task = task)

    def exec_remote(self, env, name, options = None, display = True):
        if not options:
            options = {}

        result = self.get_action_result()
        command = self.registry.find_command(name, self)
        command.mute = self.mute
        success = True

        command.options.add('environment_host', self.environment_host, False)

        options = {
            key: options[key] for key in options if key not in (
                'environment_host',
                'local',
                'version',
                'reverse_status'
            )
        }
        command.log_init(options)

        def message_callback(data):
            msg = self.create_message(data, decrypt = True)

            if (display and self.verbosity > 0) or isinstance(msg, messages.ErrorMessage):
                msg.display()

            result.add(msg)
            command.queue(msg)

        try:
            api = client.API(env.host, env.port, env.user, env.token,
                params_callback = command.preprocess_handler,
                message_callback = message_callback
            )
            api.execute(name, options)
            command.postprocess_handler(result)

            if result.aborted:
                success = False
                raise CommandError()
        finally:
            if command.log_result:
                command.log_status(success)

        return result


    def preprocess(self, params):
        # Override in subclass
        pass

    def preprocess_handler(self, params):
        self.preprocess(params)

    def postprocess(self, result):
        # Override in subclass
        pass

    def postprocess_handler(self, result):
        if not result.aborted:
            self.postprocess(result)


    def handle(self, options, primary = False, task = None):
        width = Runtime.width()
        env = self.get_env()
        success = True

        self.log_init(self.options.export(), task)
        try:
            if not self.local and env and env.host and self.server_enabled() and self.remote_exec():
                if primary and self.display_header() and self.verbosity > 1:
                    self.data("> {} env ({})".format(
                            self.key_color(settings.DATABASE_PROVIDER),
                            self.key_color(env.host)
                        ),
                        env.name
                    )
                    self.info("=" * width)

                if primary:
                    self.confirm()
                self.exec_remote(env, self.get_full_name(), options, display = True)
            else:
                if primary and self.display_header() and self.verbosity > 1:
                    self.data("> {} env".format(
                            settings.DATABASE_PROVIDER
                        ),
                        env.name
                    )
                    self.info("=" * width)

                if primary and settings.CLI_EXEC:
                    self.confirm()
                try:
                    if not self.set_periodic_task():
                        self.run_exclusive(self.lock_id, self.exec,
                            error_on_locked = self.lock_error,
                            wait = not self.lock_no_wait,
                            timeout = self.lock_timeout,
                            interval = self.lock_interval
                        )

                except Exception as e:
                    success = False
                    raise e
                finally:
                    if self.log_result:
                        self.log_status(success)

                    if primary:
                        self.send_notifications(success)

        except CommandError as e:
            if not self.reverse_status:
                raise e
            return
        if self.reverse_status:
            self.error("")


    def handle_api(self, options):
        env = self.get_env()
        success = True

        logger.debug("Running API command: {}\n\n{}".format(self.get_full_name(), yaml.dump(options)))

        self.log_init(options)
        action = threading.Thread(target = self._exec_wrapper)
        action.start()

        logger.debug("Command thread started: {}".format(self.get_full_name()))

        try:
            while True:
                time.sleep(0.25)
                logger.debug("Checking messages")

                for data in iter(self.messages.get, None):
                    msg = self.create_message(data, decrypt = False)
                    if isinstance(msg, messages.ErrorMessage):
                        success = False

                    package = msg.to_package()
                    yield package

                if not action.is_alive():
                    logger.debug("Command thread is no longer active")
                    break
        except Exception as e:
            logger.warning("Command transport exception occured: {}".format(e))
            raise e
        finally:
            logger.debug("User disconnected")
            self.disconnected = True
            #connection.close()
