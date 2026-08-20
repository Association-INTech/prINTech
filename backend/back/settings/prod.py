from os import environ

from django.core.exceptions import ImproperlyConfigured

from .base import *


def required_env(name):
    value = environ.get(name)
    if not value:
        raise ImproperlyConfigured(f'{name} must be set')
    return value


DATABASES = {
    'default': {
        'ENGINE': environ.get('DEFAULT_DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': required_env('DEFAULT_DB_NAME'),
        'USER': required_env('DEFAULT_DB_USER'),
        'PASSWORD': required_env('DEFAULT_DB_PASSWORD'),
        'HOST': required_env('DEFAULT_DB_HOST'),
        'PORT': environ.get('DEFAULT_DB_PORT', '5432'),
    }
}

ALLOWED_HOSTS = [
    host.strip()
    for host in required_env('DJANGO_ALLOWED_HOSTS').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

CACHES = {
    'default': {
        'BACKEND': environ.get('DJANGO_CACHE_BACKEND', 'django.core.cache.backends.filebased.FileBasedCache'),
        'LOCATION': environ.get('DJANGO_CACHE_LOCATION', str(SITE_ROOT / 'cache')),
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = environ.get('DJANGO_SECURE_SSL_REDIRECT', 'true').lower() == 'true'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = int(environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'true').lower() == 'true'
SECURE_HSTS_PRELOAD = environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'true').lower() == 'true'
