from django.conf import settings
from django.db import connection

from .display import format_exception_info

import billiard as multiprocessing
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
                        wrapper, callback, args, kwargs = self.tasks.get(True, 0.05)
                        try:
                            wrapper(callback, args, kwargs)
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

    def __init__(self, count = None):
        self.tasks = queue.Queue()
        self.workers = {}

        if count is None:
            count = settings.THREAD_COUNT
        for index in range(count):
            self.workers[index] = WorkerThread(self.tasks)

    def exec(self, wrapper, callback, args, kwargs):
        self.tasks.put((wrapper, callback, args, kwargs))

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

    def raise_errors(self, command = None, error_cls = None):
        if error_cls is None:
            error_cls = ParallelError

        if self.errors:
            messages = []

            for thread in self.errors:
                if command:
                    command.error(thread.error, prefix = "[ {} ]".format(thread.name), traceback = thread.traceback, terminate = False)
                else:
                    messages.append("[ {} ] - {}:\n\n{}".format(thread.name, thread.error, "\n".join(thread.traceback)))

            if messages:
                raise error_cls("\n\n".join(messages) if not command else '')
            raise error_cls()


    def add_result(self, name, result):
        with self.thread_lock:
            self.data.append(ThreadResult(str(name), result))

    def add_error(self, name, error):
        with self.thread_lock:
            self.errors.append(ThreadError(str(name), error))


class Parallel(object):

    def __init__(self, name = None, disable_parallel = None, thread_count = None, command = None, error_cls = None):
        self.name = name
        self.disable_parallel = disable_parallel
        self.command = command
        self.error_cls = error_cls

        if self.disable_parallel is None:
            self.disable_parallel = not settings.MANAGER.runtime.parallel()

        self.results = ThreadResults()

        if not self.disable_parallel:
            self.threads = ThreadPool(thread_count)


    def exec(self, callback, *args, **kwargs):
        if not self.disable_parallel:
            self.threads.exec(self._exec, callback, args, kwargs)
        else:
            self._exec(callback, args, kwargs)

    def _exec(self, callback, args, kwargs):
        try:
            result = callback(*args, **kwargs)
            self.results.add_result(args[0] if args else self.name, result)

        except Exception as e:
            self.results.add_error(args[0] if args else self.name, e)


    def wait(self, raise_errors = True):
        if not self.disable_parallel:
            self.threads.wait()
            self.threads.terminate()

        if raise_errors:
            self.results.raise_errors(self.command, self.error_cls)
        return self.results


    @classmethod
    def list(cls, items, callback, *args, disable_parallel = None, thread_count = None, command = None, error_cls = None, raise_errors = True, **kwargs):
        count = len(list(items))

        if (thread_count and count < thread_count) or (not thread_count and count < settings.THREAD_COUNT):
            thread_count = count

        parallel = cls(
            disable_parallel = disable_parallel,
            thread_count = thread_count,
            command = command,
            error_cls = error_cls
        )
        if count > 0:
            for item in items:
                parallel.exec(callback, item, *args, **kwargs)

            return parallel.wait(raise_errors = raise_errors)
        return parallel.results


    @classmethod
    def processes(cls, items, callback, *args, disable_parallel = None, command = None, error_cls = None, **kwargs):
        process_map = {}

        if isinstance(items, (int, str)):
            indexes = list(range(0, int(items)))
        else:
            indexes = list(range(0, len(items)))

        if error_cls is None:
            error_cls = ParallelError

        def process_callback(index, *process_args, **process_kwargs):
            item = items[index] if isinstance(items, (list, tuple)) else None

            process = multiprocessing.Process(
                daemon = True,
                target = callback,
                args = [ item, *process_args ] if item is not None else process_args,
                kwargs = process_kwargs
            )
            process_map[index] = process

            process.start()
            process.join()

            if process.exitcode != 0:
                raise error_cls("Process {} failed: {}".format(index, item))
        try:
            results = cls.list(indexes, process_callback, *args,
                disable_parallel = disable_parallel,
                thread_count = len(indexes),
                command = command,
                error_cls = error_cls,
                **kwargs
            )
        finally:
            for index, process in process_map.items():
                process.terminate()
                process.join()

        return results
