from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.db.backends.postgresql import base as postgresql


class DatabaseWrapper(postgresql.DatabaseWrapper):

    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS):
        super().__init__(settings_dict, alias)

    def get_new_connection(self, conn_params):
        with settings.DB_LOCK:
            return super().get_new_connection(conn_params)
