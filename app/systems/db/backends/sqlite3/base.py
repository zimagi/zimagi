from django.db.backends.sqlite3 import base as sqlite3

from systems.db.backends import mixins


class DatabaseWrapper(mixins.DatabaseRecoveryMixin, sqlite3.DatabaseWrapper):
    
    def connect(self):
        super().connect()
        self.load_file()
    
    def close(self):
        self.save_file()
        super().close()
