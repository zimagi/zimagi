from django.conf import settings

from systems.db import manager
from .base import DataMixin


class DatabaseMixin(DataMixin):

    @property
    def db(self):
        if not getattr(self, '_cached_db_manager', None):
            self._cached_db_manager = manager.DatabaseManager()
        return self._cached_db_manager


    def parse_db_packages(self, optional = True, help_text = 'one or more database package names'):
        self.parse_variables('db_packages', optional, str, help_text,
            value_label = 'NAME',
        )

    @property
    def db_packages(self):
        packages = self.options.get('db_packages', None)
        if not packages:
            packages = [ settings.DB_PACKAGE_ALL_NAME ]
        return packages
