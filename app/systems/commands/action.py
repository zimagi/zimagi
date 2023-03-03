from django.conf import settings
from django.core.management.base import CommandError

from systems.manage.task import CommandAborted
from systems.commands.index import CommandMixin
from systems.commands.mixins import exec
from systems.commands import base, messages
from utility.data import Collection
from utility import display

import threading
import re
import logging
import copy
import yaml
import getpass
import zimagi


logger = logging.getLogger(__name__)


def primary(name, options = None, user = None, log = False):
    command = ActionCommand(name)
    command.set_option_defaults()

    if user:
        if isinstance(user, str):
            user = command._user.retrieve(user)
        command._user.set_active_user(user)

    if options:
        command.set_options(options, custom = True, clear = False)
    if log:
        command.log_init()

    return command

def child(parent, name, options = None, log = True):
    command = ActionCommand(name, parent)
    command.set_option_defaults()

    if options:
        command.set_options(options, custom = True, clear = False)
    if log:
        command.log_init()

    return command


class ReverseStatusError(Exception):
    pass


class ActionCommand(
    exec.ExecMixin,
    CommandMixin('log'),
    CommandMixin('schedule'),
    CommandMixin('notification'),
    base.BaseCommand
):
    lock = threading.Lock()


    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass


    def __init__(self, name, parent = None):
        super().__init__(name, parent)

        self.disconnected = False
        self.log_result = True
        self.notification_messages = []

        self.action_result = self.get_action_result()


    def disable_logging(self):
        with self.lock:
            self.log_result = False

    def disconnect(self):
        with self.lock:
            self.disconnected = True

    def connected(self):
        with self.lock:
            return not self.disconnected


    def queue(self, msg, log = True):
        data = super().queue(msg)
        if self.log_result:
            self.publish_message(data, include = log)
            self.log_message(data, log = log)

        self.notification_messages.append(
            self.raw_text(msg.format(disable_color = True))
        )
        self.action_result.add(msg)
        return data


    def get_action_result(self):
        return zimagi.command.CommandResponse()

    def display_header(self):
        return True


    def get_task_retries(self):
        return 0


    def parse_base(self, addons = None):

        def action_addons():
            # Operations
            if settings.QUEUE_COMMANDS:
                self.parse_push_queue()
                self.parse_async_exec()
                self.parse_worker_retries()

            if settings.QUEUE_COMMANDS or self.server_enabled():
                self.parse_worker_type()

            self.parse_local()
            self.parse_reverse_status()

            # Locking
            self.parse_lock_id()
            self.parse_lock_error()
            self.parse_lock_timeout()
            self.parse_lock_interval()
            self.parse_run_once()

            if self.server_enabled():
                # Scheduling
                self.parse_schedule()
                self.parse_schedule_begin()
                self.parse_schedule_end()

                # Notifications
                self.parse_command_notify()
                self.parse_command_notify_failure()

            if callable(addons):
                addons()

        super().parse_base(action_addons)



    def parse_worker_type(self):
        self.parse_variable('worker_type', '--worker', str,
            'machine type of worker processor to run command',
            value_label = 'MACHINE',
            default = self.spec.get('worker_type', 'default'),
            tags = ['system']
        )

    @property
    def worker_type(self):
        return self.options.get('worker_type')

    def parse_push_queue(self):
        self.parse_flag('push_queue', '--queue', "run command in the background and follow execution results", tags = ['system'])

    @property
    def push_queue(self):
        return self.options.get('push_queue')

    def parse_async_exec(self):
        self.parse_flag('async_exec', '--async', "return immediately letting command run in the background", tags = ['system'])

    @property
    def async_exec(self):
        return self.options.get('async_exec')


    def parse_worker_retries(self):
        self.parse_variable('worker_retries', '--retries', int,
            'maximum number of worker retries',
            value_label = 'RETRIES',
            default = self.get_task_retries(),
            tags = ['system']
        )

    @property
    def worker_retries(self):
        return self.options.get('worker_retries')


    @property
    def background_process(self):
        return settings.QUEUE_COMMANDS and (self.push_queue or self.async_exec)


    def parse_local(self):
        self.parse_flag('local', '--local', "force command to run in local environment", tags = ['system'])

    @property
    def local(self):
        return self.options.get('local')

    def parse_reverse_status(self):
        self.parse_flag('reverse_status', '--reverse-status', "reverse exit status of command (error on success)", tags = ['system'])

    @property
    def reverse_status(self):
        return self.options.get('reverse_status')


    def parse_lock_id(self):
        self.parse_variable('lock_id', '--lock', str,
            'command lock id to prevent simultanious duplicate execution',
            value_label = 'UNIQUE_NAME',
            tags = ['lock']
        )

    @property
    def lock_id(self):
        return self.options.get('lock_id')

    def parse_lock_error(self):
        self.parse_flag('lock_error', '--lock-error', 'raise an error and abort if commmand lock can not be established', tags = ['lock'])

    @property
    def lock_error(self):
        return self.options.get('lock_error')

    def parse_lock_timeout(self):
        self.parse_variable('lock_timeout', '--lock-timeout', int,
            'command lock wait timeout in seconds',
            value_label = 'SECONDS',
            default = 600,
            tags = ['lock']
        )

    @property
    def lock_timeout(self):
        return self.options.get('lock_timeout')

    def parse_lock_interval(self):
        self.parse_variable('lock_interval', '--lock-interval', int,
            'command lock check interval in seconds',
            value_label = 'SECONDS',
            default = 2,
            tags = ['lock']
        )

    @property
    def lock_interval(self):
        return self.options.get('lock_interval')


    def parse_run_once(self):
        self.parse_flag('run_once', '--run-once', "persist the lock id as a state flag to prevent duplicate executions", tags = ['lock'])

    @property
    def run_once(self):
        return self.options.get('run_once')


    def confirm(self):
        # Override in subclass
        pass

    def prompt(self):

        def _standard_prompt(parent, split = False):
            try:
                self.info('-' * self.display_width)
                value = input("Enter {}{}: ".format(parent, " (csv)" if split else ""))
                if split:
                    value = re.split('\s*,\s*', value)
            except Exception as error:
                self.error("User aborted", 'abort')

            return value

        def _hidden_verify_prompt(parent, split = False):
            try:
                self.info('-' * self.display_width)
                value1 = getpass.getpass(prompt = "Enter {}{}: ".format(parent, " (csv)" if split else ""))
                value2 = getpass.getpass(prompt = "Re-enter {}{}: ".format(parent, " (csv)" if split else ""))
            except Exception as error:
                self.error("User aborted", 'abort')

            if value1 != value2:
                self.error("Prompted {} values do not match".format(parent))

            if split:
                value1 = re.split('\s*,\s*', value1)

            return value1


        def _option_prompt(parent, option, top_level = False):
            any_override = False

            if isinstance(option, dict):
                for name, value in option.items():
                    override, value = _option_prompt(parent + [ str(name) ], value)
                    if override:
                        option[name] = value
                        any_override = True

            elif isinstance(option, (list, tuple)):
                process_list = True

                if len(option) == 1:
                    override, value = _option_prompt(parent, option[0])
                    if isinstance(option[0],  str) and option[0] != value:
                        option.extend(re.split('\s*,\s*', value))
                        option.pop(0)
                        process_list = False
                        any_override = True

                if process_list:
                    for index, value in enumerate(option):
                        override, value = _option_prompt(parent + [ str(index) ], value)
                        if override:
                            option[index] = value
                            any_override = True

            elif isinstance(option, str):
                parent = " ".join(parent).replace("_", " ")

                if option == '+prompt+':
                    option = _standard_prompt(parent)
                    any_override = True
                elif option == '++prompt++':
                    option = _standard_prompt(parent, True)
                    any_override = True
                elif option == '+private+':
                    option = _hidden_verify_prompt(parent)
                    any_override = True
                elif option == '++private++':
                    option = _hidden_verify_prompt(parent, True)
                    any_override = True

            return any_override, option

        for name, value in self.options.export().items():
            override, value = _option_prompt([ name ], value, True)
            if override:
                self.options.add(name, value)


    def exec(self):
        # Override in subclass
        pass

    def exec_local(self, name,
        options = None,
        task = None,
        primary = False
    ):
        if not options:
            options = {}

        command = self.manager.index.find_command(name, self)
        command.mute = self.mute

        if getattr(command, 'log_result', None):
            command.log_result = self.log_result

        options = command.format_fields(
            copy.deepcopy(options)
        )
        options.setdefault('debug', self.debug)
        options.setdefault('no_parallel', self.no_parallel)
        options.setdefault('no_color', self.no_color)
        options.setdefault('display_width', self.display_width)

        log_key = options.pop('_log_key', None)
        wait_keys = options.pop('_wait_keys', None)
        schedule_name = options.pop('_schedule', None)

        command.wait_for_tasks(wait_keys)
        command.set_options(options, split_secrets = False)

        if task:
            task.max_retries = command.worker_retries

        return command.handle(options,
            primary = primary,
            task = task,
            log_key = log_key,
            schedule = schedule_name
        )

    def exec_remote(self, host, name,
        options = None,
        display = True
    ):
        if not options:
            options = {}

        command = self.manager.index.find_command(name, self)
        command.mute = self.mute
        success = True

        if getattr(command, 'log_result', None):
            command.log_result = self.log_result

        remote_options = {
            key: options[key] for key in options if key not in (
                'no_color',
                'environment_host',
                'local',
                'version'
            )
        }
        remote_options.setdefault('debug', self.debug)
        remote_options.setdefault('no_parallel', self.no_parallel)
        remote_options.setdefault('display_width', self.display_width)

        command.set_options(options)
        command.log_init()

        def message_callback(message):
            message = self.create_message(message.render(), decrypt = False)

            if (display and self.verbosity > 0) or isinstance(message, messages.ErrorMessage):
                message.display(
                    debug = self.debug,
                    disable_color = self.no_color,
                    width = self.display_width
                )
            command.queue(message)

        try:
            api = host.command_api(
                options_callback = command.preprocess_handler,
                message_callback = message_callback
            )
            response = api.execute(name, **remote_options)
            command.postprocess_handler(response)

            if response.aborted:
                success = False
                raise CommandError()
        finally:
            command.log_status(success, True)

        return response


    def preprocess(self, options):
        # Override in subclass
        pass

    def preprocess_handler(self, options, primary = False):
        self.start_profiler('preprocess')
        self.preprocess(options)
        self.stop_profiler('preprocess')

    def postprocess(self, response):
        # Override in subclass
        pass

    def postprocess_handler(self, response, primary = False):
        if not response.aborted:
            self.start_profiler('postprocess')
            self.postprocess(response)
            self.stop_profiler('postprocess')


    def handle(self, options,
        primary = False,
        task = None,
        log_key = None,
        schedule = None
    ):
        reverse_status = self.reverse_status and not self.background_process
        notify = False

        try:
            width = self.display_width
            env = self.get_env()
            host = self.get_host()
            success = True

            log_key = self.log_init(
                task = task,
                log_key = log_key,
                worker = self.worker_type
            )
            if primary:
                self.check_abort()
                self._register_signal_handlers()

            if primary and (settings.CLI_EXEC or settings.SERVICE_INIT):
                self.info("-" * width, log = False)

            if not self.local and host and host.command_port and \
                (settings.CLI_EXEC or host.name != settings.DEFAULT_HOST_NAME) and \
                self.server_enabled() and self.remote_exec():

                if primary and self.display_header() and self.verbosity > 1 and not task:
                    self.data("> env ({})".format(
                            self.key_color(host.host)
                        ),
                        env.name,
                        'environment',
                        log = False
                    )

                if primary and settings.CLI_EXEC and not task:
                    self.prompt()
                    self.confirm()

                profiler_name = 'exec.remote.primary' if primary else 'exec.remote'

                self.start_profiler(profiler_name)
                self.exec_remote(host, self.get_full_name(), options, display = True)
                self.stop_profiler(profiler_name)
            else:
                if not self.check_execute(self.active_user):
                    self.error("User {} does not have permission to execute command: {}".format(self.active_user.name, self.get_full_name()))

                if primary and self.display_header() and self.verbosity > 1 and not task:
                    self.data('> env',
                        env.name,
                        'environment',
                        log = False
                    )

                if primary and not task:
                    if settings.CLI_EXEC:
                        self.prompt()
                        self.confirm()

                    if settings.CLI_EXEC or settings.SERVICE_INIT:
                        self.info("=" * width, log = False)
                        self.data("> {}".format(self.key_color(self.get_full_name())), log_key, 'log_key', log = False)
                        self.info("-" * width, log = False)
                try:
                    self.preprocess_handler(self.options, primary)
                    if not self.set_periodic_task() and not self.set_queue_task(log_key):
                        profiler_name = 'exec.local.primary' if primary else 'exec.local'

                        self.start_profiler(profiler_name)
                        self.run_exclusive(self.lock_id, self.exec,
                            error_on_locked = self.lock_error,
                            timeout = self.lock_timeout,
                            interval = self.lock_interval,
                            run_once = self.run_once
                        )
                        notify = True
                        self.stop_profiler(profiler_name)

                except Exception as error:
                    success = False
                    raise error
                finally:
                    self.postprocess_handler(self.action_result, primary)

        except Exception as error:
            if reverse_status and (not task or task.request.retries == self.worker_retries):
                return log_key
            raise error

        finally:
            real_status = not success if reverse_status else success

            self.log_status(real_status, True, schedule = schedule)
            if primary:
                self.set_status(real_status)
                if notify:
                    self.send_notifications(real_status)

            if not task or success or (not success and task.request.retries == self.worker_retries):
                self.publish_exit()

            if primary:
                self.flush()
                self.manager.cleanup()

        if reverse_status:
            raise ReverseStatusError()
        return log_key


    def _exec_wrapper(self, options):
        command_name = self.get_full_name()
        notify = False

        try:
            if settings.QUEUE_COMMANDS:
               self.options.add('push_queue', True, False)

            width = self.display_width
            log_key = self.log_init()
            success = True

            self.check_abort()

            if self.display_header() and self.verbosity > 1:
                self.info("=" * width)
                self.data("> {}".format(command_name), log_key, 'log_key')
                self.data("> active user", self.active_user.name, 'active_user')
                self.info("-" * width)

            if not self.set_periodic_task() and not self.set_queue_task(log_key):
                self.start_profiler('exec.api')
                self.run_exclusive(self.lock_id, self.exec,
                    error_on_locked = self.lock_error,
                    timeout = self.lock_timeout,
                    interval = self.lock_interval,
                    run_once = self.run_once
                )
                notify = True
                self.stop_profiler('exec.api')

        except Exception as e:
            success = False

            if not isinstance(e, (CommandError, CommandAborted)):
                self.error(e,
                    terminate = False,
                    traceback = display.format_exception_info()
                )
        finally:
            try:
                if notify:
                    self.send_notifications(success)

                self.log_status(success, True)

            except Exception as e:
                self.error(e,
                    terminate = False,
                    traceback = display.format_exception_info()
                )

            finally:
                self.set_status(success)
                self.publish_exit()
                self.manager.cleanup()
                self.flush()

                if re.match(r'^module\s+(add|create|save|remove)$', command_name):
                    self.manager.restart_scheduler()


    def handle_api(self, options):
        self._register_signal_handlers()

        logger.debug("Running API command: {}\n\n{}".format(self.get_full_name(), yaml.dump(options)))

        action = threading.Thread(target = self._exec_wrapper, args = (options,))
        action.start()

        logger.debug("Command thread started: {}".format(self.get_full_name()))

        try:
            while True:
                self.sleep(0.25)
                logger.debug("Checking messages")

                for data in iter(self.messages.get, None):
                    logger.debug("Receiving data: {}".format(data))

                    msg = self.create_message(data, decrypt = False)
                    package = msg.to_package()
                    yield package

                if not action.is_alive():
                    logger.debug("Command thread is no longer active")
                    break
        except Exception as e:
            logger.warning("Command transport exception: {}".format(e))
            raise e
        finally:
            logger.debug("User disconnected")
            self.disconnect()
            self.export_profiler_data()
