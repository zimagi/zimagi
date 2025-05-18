import queue
import threading

from . import exceptions, settings


class ParallelError(Exception):
    pass


class WorkerThread(threading.Thread):
    def __init__(self, tasks=None, target=None, args=None, kwargs=None):
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
        if self.tasks:
            while not self.terminated:
                try:
                    wrapper, callback, results, item = self.tasks.get(True, 0.05)
                    try:
                        wrapper(callback, results, item)
                    finally:
                        self.tasks.task_done()

                except queue.Empty:
                    continue

        elif self.target:
            if callable(self.target):
                self.target(self, *self.args, **self.kwargs)

    def terminate(self, timeout=None):
        self.stop_signal.set()
        super().join(timeout)

    @property
    def terminated(self):
        return self.stop_signal.isSet()


class ThreadPool:
    def __init__(self):
        self.tasks = queue.Queue()
        self.workers = {}
        for index in range(settings.THREAD_COUNT):
            self.workers[index] = WorkerThread(self.tasks)

    def exec(self, wrapper, callback, results, item):
        self.tasks.put((wrapper, callback, results, item))

    def wait(self):
        self.tasks.join()

    def terminate(self):
        for index, thread in self.workers.items():
            thread.terminate()


class ThreadError:
    def __init__(self, name, error):
        self.name = name
        self.error = error
        self.traceback = exceptions.format_exception_info()

    def __str__(self):
        return f"[{self.name}] - {self.error}\n\n** {self.traceback}"

    def __repr__(self):
        return self.__str__()


class ThreadResult:
    def __init__(self, name, result):
        self.name = name
        self.result = result

    def __str__(self):
        return f"[{self.name}] - {self.result}"

    def __repr__(self):
        return self.__str__()


class ThreadResults:
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


class Parallel:
    @classmethod
    def exec(cls, callback, results, item):
        try:
            result = callback(item)
            results.add_result(item, result)

        except Exception as e:
            results.add_error(item, e)

    @classmethod
    def list(cls, items, callback, disable_parallel=None):
        if disable_parallel is None:
            disable_parallel = not settings.PARALLEL

        results = ThreadResults()

        if not disable_parallel:
            threads = ThreadPool()

        for item in items:
            if not disable_parallel:
                threads.exec(cls.exec, callback, results, item)
            else:
                cls.exec(callback, results, item)

        if not disable_parallel:
            threads.wait()
            threads.terminate()

        return results


def exec(items, callback):
    results = Parallel.list(items, callback)

    if results.aborted:
        errors = []
        for thread in results.errors:
            errors.append("[ {} ] - {}:\n{}".format(thread.name, thread.error, "\n".join(thread.traceback)))
        raise ParallelError("\n\n".join(errors))

    return results
