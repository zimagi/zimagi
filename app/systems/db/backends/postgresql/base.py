from django.db import DEFAULT_DB_ALIAS
from django.db.backends.postgresql import base as postgresql

from systems.db.backends import mixins


class DatabaseWrapper(mixins.DatabaseRecoveryMixin, postgresql.DatabaseWrapper):
    
    def __init__(self, settings_dict, alias = DEFAULT_DB_ALIAS, allow_thread_sharing = True):
        super().__init__(settings_dict, alias, True)
