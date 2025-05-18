import functools
import logging
import threading
import time

import redis
from django.conf import settings
from utility.parallel import Parallel
from utility.time import Time

logger = logging.getLogger(__name__)


def mutex_lock_key(lock_id):
    return f"lock:{lock_id}"


def mutex_state_key(key):
    return f"state:{key}"


class MutexError(Exception):
    pass


class MutexTimeoutError(Exception):
    pass


class BaseMutex:
    thread_lock = threading.Lock()
    connection = None

    @classmethod
    def init_connection(cls):
        with cls.thread_lock:
            if settings.REDIS_MUTEX_URL and not cls.connection:
                cls.connection = redis.from_url(settings.REDIS_MUTEX_URL)
        return cls.connection


class check_mutex(BaseMutex):
    def __init__(self, lock_id, force_remove=False):
        self.lock_id = mutex_lock_key(lock_id)
        self.force_remove = force_remove

        self.redis_lock = None
        self.acquired = False

        if self.init_connection():
            self.redis_lock = redis.lock.Lock(
                self.connection, self.lock_id, timeout=settings.MUTEX_TTL_SECONDS, blocking=False, thread_local=True
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
        lock_error_message = f"Could not acquire lock: {self.lock_id}"

        if self.redis_lock:
            with self.thread_lock:
                if not self.redis_lock.acquire():
                    raise MutexError(lock_error_message)
        else:
            if not self.thread_lock.acquire():
                raise MutexError(lock_error_message)

        self.acquired = True
        settings.MANAGER.index.add_lock(self.lock_id)

    def __exit__(self, *args):
        if self.acquired or self.force_remove:
            if self.redis_lock:
                with self.thread_lock:
                    try:
                        try:
                            self.redis_lock.release()
                        except redis.lock.LockError:
                            pass

                    except redis.exceptions.LockNotOwnedError:
                        raise MutexTimeoutError(f"Lock {self.lock_id} expired before function completed")
            else:
                try:
                    self.thread_lock.release()
                except RuntimeError:
                    pass


class Mutex(BaseMutex):
    @classmethod
    def clear(cls, *keys):
        if cls.init_connection():

            def delete_key(key):
                cls.connection.delete(mutex_state_key(key))

            Parallel.list(keys, delete_key)

    @classmethod
    def set(cls, key, expire_seconds=None):
        if cls.init_connection():
            cls.connection.set(mutex_state_key(key), Time().now_string, ex=expire_seconds)

    @classmethod
    def wait(cls, *keys, timeout=600, interval=1):
        if cls.init_connection():
            start_time = time.time()
            current_time = start_time
            keys = list(keys)
            key_count = len(keys)

            for index, key in enumerate(keys):
                keys[index] = mutex_state_key(key)

            while (current_time - start_time) <= timeout:
                stored_keys = cls.connection.exists(*keys)
                if stored_keys == key_count:
                    return True

                time.sleep(interval)
                current_time = time.time()
        return False
