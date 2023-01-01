"""
Zimagi WSGI API config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
from django.core.wsgi import get_wsgi_application

from systems.models.overrides import *

import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.api")
application = get_wsgi_application()
