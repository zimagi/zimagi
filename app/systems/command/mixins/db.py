from systems.db import manager
from .base import DataMixin


class DatabaseMixin(DataMixin):

    @property
    def db(self):
        if not getattr(self, '_cached_db_manager', None):
            self._cached_db_manager = manager.DatabaseManager()
        return self._cached_db_manager
