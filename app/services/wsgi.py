"""
Zimagi WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from systems.models.overrides import *  # noqa: F401, F403
from utility.mutex import Mutex

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.full")
application = get_wsgi_application()

Mutex.set("startup_{}".format(os.environ["ZIMAGI_SERVICE"]))
