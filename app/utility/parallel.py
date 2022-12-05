from django.conf import settings
from django.db import connection

from .display import format_exception_info

import threading
import queue


class ParallelError(Exception):
    pass


class WorkerThread(threading.Thread):

    def __init__(self, tasks = None, target = None, args = None, kwargs = None):
        if not args:
            args = []
        if not kwargs:
            kwargs = {}

        super().__init__()
        self.tasks = tasks
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.daemon = True
        self.stop_signal = threading.Event()
        self.start()

    def run(self):
        try:
            if self.tasks:
                while not self.terminated:
                    try:
                        wrapper, callback, results, item, args, kwargs = self.tasks.get(True, 0.05)
                        try:
                            wrapper(callback, results, item, args, kwargs)
                        finally:
                            self.tasks.task_done()

                    except queue.Empty:
                        continue

            elif self.target:
                if callable(self.target):
                    self.target(self, *self.args, **self.kwargs)
        finally:
            connection.close()


    def terminate(self, timeout = None):
        self.stop_signal.set()
        super().join(timeout)

    @property
    def terminated(self):
        return self.stop_signal.isSet()


class ThreadPool(object):

    def __init__(self):
        self.tasks = queue.Queue()
        self.workers = {}
        for index in range(settings.THREAD_COUNT):
            self.workers[index] = WorkerThread(self.tasks)

    def exec(self, wrapper, callback, results, item, args, kwargs):
        self.tasks.put((wrapper, callback, results, item, args, kwargs))

    def wait(self):
        self.tasks.join()

    def terminate(self):
        for index, thread in self.workers.items():
            thread.terminate()


class ThreadError(object):
    def __init__(self, name, error):
        self.name = name
        self.error = error
        self.traceback = format_exception_info()

    def __str__(self):
        return "[{}] - {}\n\n** {}".format(self.name, self.error, self.traceback)

    def __repr__(self):
        return self.__str__()

class ThreadResult(object):
    def __init__(self, name, result):
        self.name = name
        self.result = result

    def __str__(self):
        return "[{}] - {}".format(self.name, self.result)

    def __repr__(self):
        return self.__str__()


class ThreadResults(object):

    def __init__(self):
        self.thread_lock = threading.Lock()
        self.errors = []
        self.data = []

    @property
    def aborted(self):
        return len(self.errors) > 0

    def add_result(self, name, result):
        with self.thread_lock:
            self.data.append(ThreadResult(str(name), result))

    def add_error(self, name, error):
        with self.thread_lock:
            self.errors.append(ThreadError(str(name), error))


class Parallel(object):

    @classmethod
    def _exec(cls, callback, results, item, args, kwargs):
        try:
            result = callback(item, *args, **kwargs)
            results.add_result(item, result)

        except Exception as e:
            results.add_error(item, e)


    @classmethod
    def list(cls, items, callback, *args, disable_parallel = None, **kwargs):
        if disable_parallel is None:
            disable_parallel = not settings.MANAGER.runtime.parallel()

        results = ThreadResults()

        if not disable_parallel:
            threads = ThreadPool()

        for item in items:
            if not disable_parallel:
                threads.exec(cls._exec, callback, results, item, args, kwargs)
            else:
                cls._exec(callback, results, item, args, kwargs)

        if not disable_parallel:
            threads.wait()
            threads.terminate()

        return results
