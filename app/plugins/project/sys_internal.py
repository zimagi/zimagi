from django.conf import settings

from .base import BaseProvider


class Provider(BaseProvider):

    def project_path(self, name, ensure = True):
        return settings.APP_DIR
