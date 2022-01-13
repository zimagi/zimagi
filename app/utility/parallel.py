from .runtime import Runtime
from .display import format_exception_info

import threading


class ThreadError(object):
    def __init__(self, name, error):
        self.name = name
        self.error = error
        self.traceback = format_exception_info()

    def __str__(self):
        return "[{}] - {}\n\n** {}".format(self.name, self.error, "\n".join(self.traceback))

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

    thread_lock = threading.Lock()


    def __init__(self):
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
    def list(cls, items, callback, disable_parallel = None):
        results = ThreadResults()

        def _exec(item):
            try:
                results.add_result(item, callback(item))
            except Exception as error:
                results.add_error(item, error)

        if disable_parallel is None:
            disable_parallel = not Runtime.parallel()

        if items:
            if not disable_parallel:
                threads = []

                for item in items:
                    thread = threading.Thread(target = _exec, args = [ item ])
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()
            else:
                for item in items:
                    _exec(item)

        return results
