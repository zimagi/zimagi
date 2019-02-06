from django.conf import settings

from .base import BaseProjectProvider


class Internal(BaseProjectProvider):

    def project_path(self, name):
        return settings.APP_DIR
