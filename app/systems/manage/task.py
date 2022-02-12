from django.conf import settings

from utility.data import Collection, flatten, dump_json, load_json
from utility.parallel import Parallel

import os
import signal
import threading
import time
import redis


def command_status_key(key):
    return "command:status:{}".format(key)

def command_control_key(key):
    return "command:control:{}".format(key)

def channel_abort_key(key):
    return "channel:abort:{}".format(key)

def channel_message_key(key):
    return "channel:messages:{}".format(key)

def channel_communication_key(key):
    return "channel:communication:{}".format(key)


class CommandAborted(Exception):
    pass


def abort_handler(signal, frame):
    raise CommandAborted()

signal.signal(signal.SIGUSR1, abort_handler)


class ControlSensor(threading.Thread):

    def __init__(self, manager, key):
        super().__init__()
        self.manager = manager
        self.key = key

        self.daemon = True
        self.stop_signal = threading.Event()
        self.start()


    def run(self):
        if self.manager.task_connection():
            subscription = self.manager._task_connection.pubsub(ignore_subscribe_messages = True)
            try:
                subscription.subscribe(channel_abort_key(self.key))

                while not self.terminated:
                    message = subscription.get_message()
                    if message and message['type'] == 'message':
                        if message['data'] == self.manager.TASK_ABORT_TOKEN:
                            os.kill(os.getpid(), signal.SIGUSR1)

                    time.sleep(0.25)
            finally:
                self.manager.delete_task_control(self.key)
                subscription.close()


    def terminate(self, timeout = None):
        self.stop_signal.set()
        super().join(timeout)

    @property
    def terminated(self):
        return self.stop_signal.isSet()


class ManagerTaskMixin(object):

    TASK_EXIT_TOKEN = '<<<EXIT>>>'
    TASK_ABORT_TOKEN = '<<<ABORT>>>'


    def __init__(self):
        super().__init__()
        self.sensors = Collection()


    def cleanup(self):
        self.terminate_sensors()
        if self.task_connection():
            self._task_connection.close()


    def task_connection(self):
        if not getattr(self, '_task_connection', None):
            if settings.REDIS_TASK_URL:
                self._task_connection = redis.from_url(
                    settings.REDIS_TASK_URL,
                    encoding = 'utf-8',
                    decode_responses = True
                )
            else:
                self._task_connection = None
        return self._task_connection


    def get_sensor(self, key):
        if key not in self.sensors:
            self.sensors[key] = ControlSensor(self, key)
        return self.sensors[key]

    def terminate_sensors(self):
        def _terminate(key):
            self.sensors[key].terminate()
        Parallel.list(self.sensors.export().keys(), _terminate)


    def get_task_status(self, key):
        if self.task_connection():
            return self._task_connection.get(command_status_key(key))
        return None

    def set_task_status(self, key, status):
        if self.task_connection():
            self._task_connection.set(command_status_key(key), status)
            return True
        return False

    def delete_task_status(self, key):
        if self.task_connection():
            self._task_connection.delete(command_status_key(key))

    def delete_task_statuses(self, keys):
        if self.task_connection() and keys:
            Parallel.list(
                list(set(flatten(keys))),
                self.delete_task_status
            )


    def get_task_control(self, key):
        if self.task_connection():
            return self._task_connection.get(command_control_key(key))
        return None

    def set_task_control(self, key, control):
        if self.task_connection() and not self.get_task_status(key):
            self._task_connection.set(command_control_key(key), control)
            return True
        return False

    def delete_task_control(self, key):
        if self.task_connection():
            self._task_connection.delete(command_control_key(key))

    def delete_task_controls(self, keys):
        if self.task_connection() and keys:
            Parallel.list(
                list(set(flatten(keys))),
                self.delete_task_control
            )


    def follow_task(self, key, message_callback = None, status_check_interval = 1000, sleep_secs = 0.01):
        if self.task_connection():
            status = self.get_task_status(key)
            if status:
                return status

            subscription = self._task_connection.pubsub(ignore_subscribe_messages = True)
            subscription.subscribe(channel_message_key(key))
            status_check_index = 0

            while True:
                message = subscription.get_message()
                if message:
                    if message['type'] == 'message':
                        if message['data'] == self.TASK_EXIT_TOKEN:
                            break
                        if callable(message_callback):
                            message_callback(load_json(message['data']))

                if status_check_index > status_check_interval:
                    if self.get_task_status(key):
                        break
                    else:
                        status_check_index = 0

                time.sleep(sleep_secs)
                status_check_index += 1

            subscription.close()
            return self.get_task_status(key)
        return None

    def wait_for_tasks(self, keys):
        if self.task_connection() and keys:
            def wait_for_task(key):
                while not self.get_task_status(key):
                    time.sleep(0.5)

            Parallel.list(
                list(set(flatten(keys))),
                wait_for_task
            )


    def publish_task_message(self, key, data):
        if self.task_connection():
            self._task_connection.publish(channel_message_key(key), dump_json(data))

    def publish_task_exit(self, key, status):
        if self.set_task_status(key, status):
            self._task_connection.publish(channel_message_key(key), self.TASK_EXIT_TOKEN)


    def check_task_abort(self, key):
        if self.task_connection() and not self.get_task_status(key):
            control = self.get_task_control(key)
            if control:
                self.delete_task_control(key)
                if control == self.TASK_ABORT_TOKEN:
                    os.kill(os.getpid(), signal.SIGUSR1)

    def publish_task_abort(self, key):
        if self.set_task_control(key, self.TASK_ABORT_TOKEN):
            self._task_connection.publish(channel_abort_key(key), self.TASK_ABORT_TOKEN)
