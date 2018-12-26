from django.db.backends.postgresql import base as postgresql

from systems.db.backends import mixins


class DatabaseWrapper(mixins.DatabaseRecoveryMixin, postgresql.DatabaseWrapper):
    pass