from django.conf import settings
from django.core.management.base import CommandError

from utility.config import RuntimeConfig
from utility.display import format_exception_info

import threading
import queue


class WorkerThread(threading.Thread):

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            wrapper, callback, results, item = self.tasks.get()
            try:
                wrapper(callback, results, item)
            finally:
                self.tasks.task_done()


class ThreadPool(object):

    def __init__(self):
        self.tasks = queue.Queue()
        self.workers = {}
        for index in range(settings.THREAD_COUNT):
            self.workers[index] = WorkerThread(self.tasks)

    def exec(self, wrapper, callback, results, item):
        self.tasks.put((wrapper, callback, results, item))

    def wait(self):
        self.tasks.join()


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
    def exec(cls, callback, results, item):
        try:
            result = callback(item)
            results.add_result(item, result)

        except Exception as e:
            results.add_error(item, e)


    @classmethod
    def list(cls, items, callback):
        parallel = RuntimeConfig.parallel()
        results = ThreadResults()

        if parallel:
            threads = ThreadPool()

        for item in items:
            if parallel:
                threads.exec(cls.exec, callback, results, item)
            else:
                cls.exec(callback, results, item)

        if parallel:
            threads.wait()

        return results
