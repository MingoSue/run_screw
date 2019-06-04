"""
WSGI config for ScrewDriver project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys
from os.path import join,dirname,abspath
PROJECT_DIR = dirname(dirname(abspath(__file__)))

from django.core.wsgi import get_wsgi_application
sys.path.insert(0,PROJECT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ScrewDriver.settings')

application = get_wsgi_application()
