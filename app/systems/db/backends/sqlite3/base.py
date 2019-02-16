from django.db import DEFAULT_DB_ALIAS
from django.db.backends.sqlite3 import base as sqlite3

from systems.db.backends import mixins


class DatabaseWrapper(mixins.DatabaseRecoveryMixin, sqlite3.DatabaseWrapper):
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS, allow_thread_sharing = True):
        if not getattr(self, '_initialized', False):
            settings_dict['NAME'] = ':memory:'
            super().__init__(settings_dict, alias, True)
            self._initialized = True

    
    def connect(self):
        super().connect()
        self.load_file()
    
    def close(self):
        self.save_file()
        super().close()
