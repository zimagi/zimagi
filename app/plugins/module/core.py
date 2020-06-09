from django.conf import settings

from systems.plugins.index import BaseProvider


class Provider(BaseProvider('module', 'core')):

    def module_path(self, name, ensure = True):
        return settings.APP_DIR
