from systems.db import manager
from systems.command.index import CommandMixin


class DatabaseMixin(CommandMixin('db')):

    @property
    def db(self):
        if not getattr(self, '_cached_db_manager', None):
            self._cached_db_manager = manager.DatabaseManager()
        return self._cached_db_manager
