from django.db import DEFAULT_DB_ALIAS
from django.db.backends.postgresql import base as postgresql


class DatabaseWrapper(postgresql.DatabaseWrapper):

    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS):
        super().__init__(settings_dict, alias)
