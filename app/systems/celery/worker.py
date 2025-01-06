import os
import signal
import threading
import time

import redis
from django.conf import settings
from utility.data import ensure_list


def start_worker_manager(app):
    return WorkerManager(app)


class RedisConnectionMixin:
    def connection(self):
        if not getattr(self, "_connection", None):
            if settings.CELERY_BROKER_URL:
                self._connection = redis.from_url(settings.CELERY_BROKER_URL, encoding="utf-8", decode_responses=True)
            else:
                self._connection = None
        return self._connection

    def get_queues(self, app, worker_name):
        worker_queues = app.control.inspect().active_queues()
        if worker_queues and worker_name in worker_queues:
            return [queue_info["name"] for queue_info in worker_queues[worker_name]]
        return []

    def check_queues(self, queue_names, app=None, worker_name=None):
        # Find tasks yet to be executed
        for queue_name in ensure_list(queue_names):
            count = self.connection().llen(queue_name)
            if count and count > 0:
                return True

        if app and worker_name:
            inspector = app.control.inspect()

            # Find tasks reserved to be executed
            reserved = inspector.reserved()
            if reserved and reserved.get(worker_name, None):
                return True

            # Find tasks being executed
            active = inspector.active()
            if active and active.get(worker_name, None):
                return True

        return False


class WorkerManager(RedisConnectionMixin, threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.daemon = True
        self.stop_signal = threading.Event()
        self.start()

    def run(self):
        if not self.connection():
            return
        try:
            start_time = time.time()
            current_time = start_time

            while not self.terminated:
                if settings.WORKER_TIMEOUT > 0:
                    worker_name = os.environ.get("ZIMAGI_CELERY_NAME", None)
                    worker_queues = self.get_queues(self.app, worker_name)

                    if worker_name and worker_queues:
                        if not self.check_queues(worker_queues, app=self.app, worker_name=worker_name):
                            if (current_time - start_time) > settings.WORKER_TIMEOUT:
                                os.kill(os.getpid(), signal.SIGTERM)
                                break
                        else:
                            start_time = time.time()

                time.sleep(settings.WORKER_CHECK_INTERVAL)
                current_time = time.time()
        finally:
            self.connection().close()

    def terminate(self, timeout=None):
        self.stop_signal.set()
        super().join(timeout)

    @property
    def terminated(self):
        return self.stop_signal.isSet()
