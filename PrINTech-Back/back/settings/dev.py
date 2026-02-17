from os import environ
from pathlib import Path

from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': environ.get('DEFAULT_DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': environ.get('DEFAULT_DB_NAME', 'back'),
        'USER': environ.get('DEFAULT_DB_USER', 'back'),
        'PASSWORD': environ.get('DEFAULT_DB_PASSWORD', 'back'),
        'HOST': environ.get('DEFAULT_DB_HOST', 'localhost'),
        'PORT': environ.get('DEFAULT_DB_PORT', '5432'),
    }
}

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'debug_toolbar',
]

DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
INTERNAL_IPS = ['127.0.0.1', '0.0.0.0']
