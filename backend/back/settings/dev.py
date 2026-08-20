from os import environ

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

if environ.get('DJANGO_ENV', '').lower() == 'production':
    raise ImproperlyConfigured('back.settings.dev must not be used with DJANGO_ENV=production')

if not environ.get('DJANGO_SECRET_KEY'):
    environ['DJANGO_SECRET_KEY'] = get_random_secret_key()

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

ALLOWED_HOSTS = [host.strip() for host in environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',') if host.strip()]

INSTALLED_APPS += [
    'debug_toolbar',
]

DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
INTERNAL_IPS = ['127.0.0.1']

ALLOW_PUBLIC_SIGNUP = environ.get('DJANGO_ALLOW_PUBLIC_SIGNUP', 'true').lower() == 'true'
