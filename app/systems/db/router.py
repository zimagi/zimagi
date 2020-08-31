from django.conf import settings


class DatabaseRouter:

    def db_for_read(self, model, **hints):
        return 'default'

    def db_for_write(self, model, **hints):
        if 'write' in settings.DATABASES:
            return 'write'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
