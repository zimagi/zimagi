from django.core.management.base import CommandError

from utility.display import format_exception_info

import threading


class ThreadState(object):
    def __init__(self, item = None):
        self.item = item
        self.result = None


class ThreadError(object):
    def __init__(self, name, error):
        self.name = name
        self.error = error
        self.traceback = format_exception_info()

class ThreadResult(object):
    def __init__(self, name, result):
        self.name = name
        self.result = result


class ThreadResults(object):

    def __init__(self):
        self.thread_lock = threading.Lock()

        self.errors = []
        self.results = []

    @property
    def aborted(self):
        return len(self.errors) > 0


    def add_result(self, name, state):
        with self.thread_lock:
            self.results.append(ThreadResult(str(name), state))

    def add_error(self, name, error):
        with self.thread_lock:
            self.errors.append(ThreadError(str(name), error))


class Thread(object):

    def __init__(self, complete_callback = None, state_callback = None):
        self.thread_lock = threading.Lock()

        self.complete_callback = complete_callback
        self.state_callback = state_callback

        if not self.state_callback:
            self.state_callback = self._default_state            


    def _default_state(self, item):
        return ThreadState(item)
    

    def _wrapper(self, results, state, item, callback):
        try:
            callback(item, state)

            if self.complete_callback and callable(self.complete_callback):
                with self.thread_lock:
                    self.complete_callback(item, state)

            results.add_result(item, state)

        except Exception as e:
            results.add_error(item, e)


    def list(self, items, callback):
        results = ThreadResults()
        threads = []

        for item in items:
            state = self.state_callback(item)
            thread = threading.Thread(
                target = self._wrapper, 
                args = [results, state, item, callback]
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return results
