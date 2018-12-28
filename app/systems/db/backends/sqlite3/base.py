from django.db import DEFAULT_DB_ALIAS
from django.db.backends.sqlite3 import base as sqlite3

from systems.db.backends import mixins


class DatabaseWrapper(mixins.DatabaseRecoveryMixin, sqlite3.DatabaseWrapper):

    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS, allow_thread_sharing = True):
        settings_dict['NAME'] = ':memory:'
        super().__init__(settings_dict, alias, True)

    
    def connect(self):
        super().connect()
        self.load_file()
    
    def close(self):
        self.save_file()
        super().close()
