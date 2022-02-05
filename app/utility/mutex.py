from django.conf import settings

import redis
import threading
import functools
import logging


logger = logging.getLogger(__name__)


class MutexError(Exception):
    pass

class MutexTimeoutError(Exception):
    pass


class check_mutex(object):

    thread_lock = threading.Lock()
    connection = None


    @classmethod
    def init_connection(cls):
        with cls.thread_lock:
            if settings.REDIS_MUTEX_URL and not cls.connection:
                cls.connection = redis.from_url(settings.REDIS_MUTEX_URL)
        return cls.connection


    def __init__(self, lock_id):
        self.lock_id = lock_id
        self.redis_lock = None
        self.acquired = False

        if self.init_connection():
            self.redis_lock = redis.lock.Lock(
                self.connection,
                self.lock_id,
                timeout = settings.MUTEX_TTL_SECONDS,
                blocking = False,
                thread_local = True
            )


    def __call__(self, function):
        def wrapper(*args, **kwargs):
            try:
                with self:
                    result = function(*args, **kwargs)
                return result

            except MutexError as error:
                logger.debug(error)
                raise error

        functools.update_wrapper(wrapper, function)
        return wrapper


    def __enter__(self):
        lock_error_message = "Could not acquire lock: {}".format(self.lock_id)

        if self.redis_lock:
            with self.thread_lock:
                if not self.redis_lock.acquire():
                    raise MutexError(lock_error_message)
        else:
            if not self.thread_lock.acquire(blocking = False):
                raise MutexError(lock_error_message)

        self.acquired = True

    def __exit__(self, *args):
        if self.acquired:
            if self.redis_lock:
                with self.thread_lock:
                    try:
                        self.redis_lock.release()

                    except redis.exceptions.LockNotOwnedError:
                        raise MutexTimeoutError("Lock {} expired before function completed".format(self.lock_id))
            else:
                self.thread_lock.release()
