from django.db import DEFAULT_DB_ALIAS
from django.db.backends.mysql import base as mysql


class DatabaseWrapper(mysql.DatabaseWrapper):

    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS):
        super().__init__(settings_dict, alias)
