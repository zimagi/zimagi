"""
API WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""
from django.core.wsgi import get_wsgi_application

from utility.runtime import Runtime

import os

Runtime.api(True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.api.settings")
application = get_wsgi_application()
