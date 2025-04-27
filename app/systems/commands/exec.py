import copy
import getpass
import logging
import re
import threading
import time

import yaml
from django.conf import settings
from django.core.management.base import CommandError
from systems.commands import base, messages
from systems.commands.index import CommandMixin
from systems.commands.mixins import exec
from systems.api.mcp.client import MCPClient
from systems.manage.task import CommandAborted
from utility import display
from utility.data import create_token

import zimagi

logger = logging.getLogger(__name__)


class ReverseStatusError(Exception):
    pass


class ExecCommand(
    exec.ExecMixin, CommandMixin("log"), CommandMixin("schedule"), CommandMixin("notification"), base.BaseCommand
):
    lock = threading.Lock()

    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass

    def __init__(self, name, parent=None):
        super().__init__(name, parent)

        self.log_result = True
        self.notification_messages = []

        self.disconnected = False
        self.exec_result = self.get_exec_result()

    def signal_shutdown(self):
        try:
            if not self.background_process:
                self.set_status(False)
                self.log_status(False)
                self.publish_exit()

        except Exception as error:
            logger.info(f"Signal shutdown for base executable command errored with: {error}")

        super().signal_shutdown()

    def disconnect(self):
        with self.lock:
            self.disconnected = True

    def connected(self):
        with self.lock:
            return not self.disconnected

    def get_exec_result(self):
        return zimagi.command.CommandResponse()

    def disable_logging(self):
        with self.lock:
            self.log_result = False

    def queue(self, msg, log=True):
        data = super().queue(msg)
        if self.log_result:
            self.publish_message(data, include=log)
            self.log_message(data, log=log)

        self.notification_messages.append(self.raw_text(msg.format(disable_color=True)))
        self.exec_result.add(msg)
        return data

    def display_header(self):
        return True

    def parse_base(self, addons=None, add_api_fields=False):
        def exec_addons():
            # Operations
            self.parse_local()
            self.parse_reverse_status()

            if self.background_process:
                self.parse_async_exec()
                self.parse_worker_task_retries()
                self.parse_worker_task_priority()

            if self.background_process or self.server_enabled():
                self.parse_worker_type()

            # Locking
            self.parse_lock_id()
            self.parse_lock_error()
            self.parse_lock_timeout()
            self.parse_lock_interval()
            self.parse_run_once()

            # Notifications
            self.parse_command_notify()
            self.parse_command_notify_failure()

            if callable(addons):
                addons()

        super().parse_base(exec_addons, add_api_fields)

    def get_worker_type(self):
        return "default"

    def parse_worker_type(self):
        self.parse_variable(
            "worker_type",
            "--worker",
            str,
            "machine type of worker processor to run command",
            value_label="MACHINE",
            default=self.get_worker_type(),
            tags=["system"],
        )

    @property
    def worker_type(self):
        return self.options.get("worker_type")

    def get_task_retries(self):
        return 0

    def parse_worker_task_retries(self):
        self.parse_variable(
            "task_retries",
            "--retries",
            int,
            "maximum number of worker retries",
            value_label="RETRIES",
            default=self.get_task_retries(),
            tags=["system"],
        )

    @property
    def worker_task_retries(self):
        return self.options.get("task_retries")

    def get_task_priority(self):
        return settings.WORKER_DEFAULT_TASK_PRIORITY

    def parse_worker_task_priority(self):
        self.parse_variable(
            "task_priority",
            "--task-priority",
            int,
            "[ 0 - 9 ] worker task priority (less equals higher priority)",
            value_label="PRIORITY",
            default=self.get_task_priority(),
            tags=["system"],
        )

    @property
    def worker_task_priority(self):
        return self.options.get("task_priority")

    def parse_async_exec(self):
        self.parse_flag("async_exec", "--async", "return immediately letting command run in the background", tags=["system"])

    @property
    def async_exec(self):
        return self.options.get("async_exec")

    def parse_reverse_status(self):
        self.parse_flag(
            "reverse_status", "--reverse-status", "reverse exit status of command (error on success)", tags=["system"]
        )

    @property
    def reverse_status(self):
        return self.options.get("reverse_status")

    def get_run_background(self):
        return True

    @property
    def background_process(self):
        return settings.QUEUE_COMMANDS and self.get_run_background()

    def parse_local(self):
        self.parse_flag("local", "--local", "force command to run in local environment", tags=["system"])

    @property
    def local(self):
        return self.options.get("local")

    def parse_lock_id(self):
        self.parse_variable(
            "lock_id",
            "--lock",
            str,
            "command lock id to prevent simultanious duplicate execution",
            value_label="UNIQUE_NAME",
            tags=["lock"],
        )

    @property
    def lock_id(self):
        return self.options.get("lock_id")

    def parse_lock_error(self):
        self.parse_flag(
            "lock_error", "--lock-error", "raise an error and abort if commmand lock can not be established", tags=["lock"]
        )

    @property
    def lock_error(self):
        return self.options.get("lock_error")

    def parse_lock_timeout(self):
        self.parse_variable(
            "lock_timeout",
            "--lock-timeout",
            int,
            "command lock wait timeout in seconds",
            value_label="SECONDS",
            default=600,
            tags=["lock"],
        )

    @property
    def lock_timeout(self):
        return self.options.get("lock_timeout")

    def parse_lock_interval(self):
        self.parse_variable(
            "lock_interval",
            "--lock-interval",
            int,
            "command lock check interval in seconds",
            value_label="SECONDS",
            default=2,
            tags=["lock"],
        )

    @property
    def lock_interval(self):
        return self.options.get("lock_interval")

    def parse_run_once(self):
        self.parse_flag(
            "run_once", "--run-once", "persist the lock id as a state flag to prevent duplicate executions", tags=["lock"]
        )

    @property
    def run_once(self):
        return self.options.get("run_once")

    def confirm(self):
        # Override in subclass
        pass

    def prompt(self):
        def _standard_prompt(parent, split=False):
            try:
                self.separator("-", system=True)
                value = input("Enter {}{}: ".format(parent, " (csv)" if split else ""))
                if split:
                    value = re.split(r"\s*,\s*", value)
            except Exception as error:
                self.error("User aborted", "abort")

            return value

        def _hidden_verify_prompt(parent, split=False):
            try:
                self.separator("-", system=True)
                value1 = getpass.getpass(prompt="Enter {}{}: ".format(parent, " (csv)" if split else ""))
                value2 = getpass.getpass(prompt="Re-enter {}{}: ".format(parent, " (csv)" if split else ""))
            except Exception as error:
                self.error("User aborted", "abort")

            if value1 != value2:
                self.error(f"Prompted {parent} values do not match")

            if split:
                value1 = re.split(r"\s*,\s*", value1)

            return value1

        def _option_prompt(parent, option, top_level=False):
            any_override = False

            if isinstance(option, dict):
                for name, value in option.items():
                    override, value = _option_prompt(parent + [str(name)], value)
                    if override:
                        option[name] = value
                        any_override = True

            elif isinstance(option, (list, tuple)):
                process_list = True

                if len(option) == 1:
                    override, value = _option_prompt(parent, option[0])
                    if isinstance(option[0], str) and option[0] != value:
                        option.extend(re.split(r"\s*,\s*", value))
                        option.pop(0)
                        process_list = False
                        any_override = True

                if process_list:
                    for index, value in enumerate(option):
                        override, value = _option_prompt(parent + [str(index)], value)
                        if override:
                            option[index] = value
                            any_override = True

            elif isinstance(option, str):
                parent = " ".join(parent).replace("_", " ")

                if option == "+prompt+":
                    option = _standard_prompt(parent)
                    any_override = True
                elif option == "++prompt++":
                    option = _standard_prompt(parent, True)
                    any_override = True
                elif option == "+private+":
                    option = _hidden_verify_prompt(parent)
                    any_override = True
                elif option == "++private++":
                    option = _hidden_verify_prompt(parent, True)
                    any_override = True

            return any_override, option

        for name, value in self.options.export().items():
            override, value = _option_prompt([name], value, True)
            if override:
                self.options.add(name, value)

    @property
    def mcp(self):
        if not getattr(self, "_mcp_client", None):
            self._mcp_client = MCPClient(self)
        return self._mcp_client

    def listen(self, channel, timeout=None, block_sec=10, state_key=None, terminate_callback=None):
        if not timeout:
            timeout = settings.AGENT_MAX_LIFETIME

        return self.manager.listen(
            channel, timeout=timeout, block_sec=block_sec, state_key=state_key, terminate_callback=terminate_callback
        )

    def submit(self, channel, message, timeout=None):
        return_channel = f"command:submit:{self.log_entry.name}:{time.time_ns()}-{create_token(5)}"
        self.send(channel, message, return_channel)
        try:
            for package in self.listen(return_channel, timeout=timeout):
                return package.message
        finally:
            self.delete_stream(return_channel)

    def collect(self, channel, message, timeout=None, quantity=None):
        return_channel = f"command:collect:{self.log_entry.name}:{time.time_ns()}-{create_token(5)}"
        self.send(channel, message, return_channel)
        try:
            index = 0
            for package in self.listen(return_channel, timeout=timeout):
                yield package.message
                if quantity:
                    index += 1
                    if index == quantity:
                        return
        finally:
            self.delete_stream(return_channel)

    def send(self, channel, message, sender=None):
        if sender is None:
            sender = self.service_id

        return self.manager.send(channel, message, sender=sender)

    def delete_stream(self, channel):
        return self.manager.delete_stream(channel)

    def exec(self):
        # Override in subclass
        pass

    def exec_local(self, name, options=None, task=None, primary=False):
        if not options:
            options = {}

        command = self.manager.index.find_command(name, self)
        command.mute = self.mute

        if getattr(command, "log_result", None):
            command.log_result = self.log_result

        if not command.background_process:
            options.pop("async_exec", None)
            options.pop("task_retries", None)
            options.pop("task_priority", None)

        options = command.format_fields(copy.deepcopy(options))
        options.setdefault("debug", self.debug)
        options.setdefault("no_parallel", self.no_parallel)
        options.setdefault("no_color", self.no_color)
        options.setdefault("display_width", self.display_width)

        log_key = options.pop("_log_key", None)
        wait_keys = options.pop("_wait_keys", None)
        schedule_name = options.pop("_schedule", None)

        command.wait_for_tasks(wait_keys)
        command.set_options(options, split_secrets=False)

        if task:
            task.max_retries = command.worker_task_retries

        return command.handle(options, primary=primary, task=task, log_key=log_key, schedule=schedule_name)

    def exec_remote(self, host, name, options=None, display=True, include_system_messages=True):
        if not options:
            options = {}

        command = self.manager.index.find_command(name, self)
        command.mute = self.mute
        success = True

        if getattr(command, "log_result", None):
            command.log_result = self.log_result

        remote_options = {
            key: options[key] for key in options if key not in ("no_color", "environment_host", "local", "version")
        }
        remote_options.setdefault("debug", self.debug)
        remote_options.setdefault("no_parallel", self.no_parallel)
        remote_options.setdefault("display_width", self.display_width)

        command.parse_base(add_api_fields=True)
        command.set_options(options, custom=True)
        command.log_init()

        def message_callback(message):
            message = self.create_message(message.render(), decrypt=False)

            if include_system_messages or not message.system:
                if (display and self.verbosity > 0) or isinstance(message, messages.ErrorMessage):
                    message.display(debug=self.debug, disable_color=self.no_color, width=self.display_width)
                command.queue(message)

        try:
            api = host.command_api(options_callback=command.preprocess_handler, message_callback=message_callback)
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

    def preprocess_handler(self, options, primary=False):
        self.start_profiler("preprocess")
        self.preprocess(options)
        self.stop_profiler("preprocess")

    def postprocess(self, response):
        # Override in subclass
        pass

    def postprocess_handler(self, response, primary=False):
        if not response.aborted:
            self.start_profiler("postprocess")
            self.postprocess(response)
            self.stop_profiler("postprocess")

    def run_exec_loop(self, name, exec_callback, pause=5, terminate_callback=None):
        def _default_terminate_callback():
            return False

        if terminate_callback is None:
            terminate_callback = _default_terminate_callback

        while not terminate_callback():
            self.check_abort()
            exec_callback()

            if (time.time() - self.start_time) >= settings.AGENT_MAX_LIFETIME:
                break
            else:
                self.sleep(pause)

    def handle(self, options, primary=False, task=None, log_key=None, schedule=None):
        host = self.get_host()
        log_key = self._exec_init(log_key=log_key, primary=primary, task=task)

        def callback():
            if (
                not self.local
                and host
                and (host.host == "localhost" or host.command_port)
                and (settings.CLI_EXEC or host.name != settings.DEFAULT_HOST_NAME)
                and self.server_enabled()
                and self.remote_exec()
            ):
                self._exec_local_header(log_key, primary=primary, task=task, host=host)
                self._exec_remote_handler(host, options, primary=primary)
                notify = False
            else:
                self._exec_access()
                self._exec_local_header(log_key, primary=primary, task=task)
                notify = self._exec_local_handler(log_key, primary=primary)

            return notify

        return self._exec_wrapper(
            callback,
            primary=primary,
            task=task,
            schedule=schedule,
            reverse_status=self.reverse_status and not self.background_process,
            log_key=log_key,
        )

    def handle_api(self, options, package=True):
        self._register_signal_handlers()

        logger.debug(f"Running API command: {self.get_full_name()}\n\n{yaml.dump(options)}")

        action = threading.Thread(target=self._api_exec_wrapper)
        action.start()

        logger.debug(f"Command thread started: {self.get_full_name()}")

        try:
            while True:
                self.sleep(0.25)
                logger.debug("Checking messages")

                for data in iter(self.messages.get, None):
                    logger.debug(f"Receiving data: {data}")

                    msg = self.create_message(data, decrypt=False)
                    if package:
                        msg = msg.to_package()
                    yield msg

                if not action.is_alive():
                    logger.debug("Command thread is no longer active")
                    break
        except Exception as e:
            logger.warning(f"Command transport exception: {e}")
            raise e
        finally:
            logger.debug("User disconnected")
            self.disconnect()
            self.export_profiler_data()

    def _exec_init(self, primary=True, log_key=None, task=None, signals=True):
        log_key = self.log_init(task=task, log_key=log_key, worker=self.worker_type)

        if primary:
            self.check_abort()
            self.manager.start_sensor(log_key)
            self.manager.set_command(self)
            if signals:
                self._register_signal_handlers()

        self.manager.init_task_status(log_key)
        return log_key

    def _exec_access(self):
        if not self.check_execute(self.active_user):
            self.error(f"User {self.active_user.name} does not have permission to execute command: {self.get_full_name()}")

    def _exec_local_header(self, log_key, primary=True, task=False, host=None):
        env = self.get_env()

        if primary and (settings.CLI_EXEC or settings.SERVICE_INIT):
            self.separator("-", system=True)

        if primary and self.display_header() and self.verbosity > 1 and not task:
            if host:
                self.data(
                    "> host",
                    f"{host.host}:{host.command_port}" if host.command_port else host.host,
                    "host",
                    log=False,
                    system=True,
                )
            self.data("> env", env.name, "environment", log=False, system=True)

        if primary and not task:
            if settings.CLI_EXEC:
                self.prompt()
                self.confirm()

            if not host and settings.CLI_EXEC or settings.SERVICE_INIT:
                self.separator(system=True)
                self.data(f"> {self.key_color(self.get_full_name())}", log_key, "log_key", log=False, system=True)
                self.separator("-", system=True)

    def _exec_api_header(self, log_key):
        if self.display_header() and self.verbosity > 1:
            self.separator(system=True)
            self.data(f"> {self.get_full_name()}", log_key, "log_key", system=True)
            self.data("> active user", self.active_user.name, "active_user", system=True)
            self.separator("-", system=True)

    def _exec_local_handler(self, log_key, primary=True):
        raise NotImplementedError(
            "Method _exec_local_handler must be implemented in subclasses of the Executable Command class"
        )

    def _exec_api_handler(self, log_key):
        raise NotImplementedError(
            "Method _exec_api_handler must be implemented in subclasses of the Executable Command class"
        )

    def _exec_remote_handler(self, host, options, primary=True):
        profiler_name = "exec.remote.primary" if primary else "exec.remote"
        try:
            self.start_profiler(profiler_name)
            self.exec_remote(host, self.get_full_name(), options, display=True)
        finally:
            self.stop_profiler(profiler_name)

    def _exec_wrapper(self, callback, primary=True, task=None, schedule=None, reverse_status=None, log_key=None):
        self.start_time = time.time()

        reverse_status = self.reverse_status if reverse_status is None else reverse_status
        success = True
        notify = True

        try:
            notify = callback()

        except Exception as error:
            success = False

            if reverse_status and (not task or task.request.retries == self.worker_task_retries):
                return log_key
            raise error

        finally:
            real_status = not success if reverse_status else success

            self.log_status(real_status, True, schedule=schedule)
            if primary:
                self.shutdown()
                self.set_status(real_status)
                if notify:
                    self.send_notifications(real_status)

            if not task or success or (not success and task.request.retries == self.worker_task_retries):
                self.publish_exit()
                self.manager.delete_task_status(log_key)

            if primary:
                self.flush()
                self.manager.cleanup(log_key)

        if reverse_status:
            raise ReverseStatusError()
        return log_key

    def _api_exec_wrapper(self):
        self.start_time = time.time()

        success = True
        notify = True
        log_key = self._exec_init(signals=False)

        try:
            self._exec_api_header(log_key)
            notify = self._exec_api_handler(log_key)

        except Exception as e:
            success = False

            if not isinstance(e, (CommandError, CommandAborted)):
                self.error(e, terminate=False, traceback=display.format_exception_info())
        finally:
            try:
                self.log_status(success, True)
                if notify:
                    self.send_notifications(success)

            except Exception as e:
                self.error(e, terminate=False, traceback=display.format_exception_info())

            finally:
                if settings.RESTART_SERVICES and re.match(r"^module\s+(add|create|save|remove)$", self.get_full_name()):
                    self.manager.restart_scheduler()

                self.shutdown()
                self.set_status(success)
                self.publish_exit()
                self.manager.delete_task_status(log_key)
                self.manager.cleanup(log_key)
                self.flush()
