from datetime import timedelta
from os import environ
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def env_int(name, default):
    try:
        return int(environ.get(name, default))
    except ValueError as exc:
        raise ImproperlyConfigured(f'{name} must be an integer') from exc


DJANGO_ROOT = Path(__file__).resolve(strict=True).parent.parent
SITE_ROOT = DJANGO_ROOT.parent
SITE_NAME = DJANGO_ROOT.name

DEBUG = False
TEMPLATE_DEBUG = DEBUG


ADMINS = [
    # ('Your Name', 'your_email@example.com'),
]

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'back',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '5432',
    }
}

ALLOWED_HOSTS = []
TIME_ZONE = 'Europe/Paris'
LANGUAGE_CODE = 'fr-FR'

SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOCALE_PATHS = [
    DJANGO_ROOT / 'locale'
]

MEDIA_ROOT = DJANGO_ROOT / 'media'
MEDIA_URL = '/media/'
STATIC_ROOT = SITE_ROOT / 'assets'
STATIC_URL = '/site_media/'
STATICFILES_DIRS = [
    DJANGO_ROOT / 'static',
]
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
SECRET_KEY = environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set')

MAX_PRINT_UPLOAD_BODY_SIZE = env_int('DJANGO_MAX_PRINT_UPLOAD_BODY_SIZE', 105 * 1024 * 1024)
MAX_MANUAL_CREDIT_OPERATION_AMOUNT = env_int('DJANGO_MAX_MANUAL_CREDIT_OPERATION_AMOUNT', 200)
ALLOW_PUBLIC_SIGNUP = environ.get('DJANGO_ALLOW_PUBLIC_SIGNUP', 'false').lower() == 'true'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

######################

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'back.apps.api.middleware.UploadSizeLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


#####################

ROOT_URLCONF = '%s.urls' % SITE_NAME
WSGI_APPLICATION = '%s.wsgi.application' % SITE_NAME
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 'django.contrib.admindocs',
]

THIRD_PARTY_APPS = [
    'django_extensions',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

LOCAL_APPS = [
    'back',
    'back.apps.api.apps.ApiConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

#################
AUTH_USER_MODEL = "api.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'printech-local-throttle-cache',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': environ.get('DRF_THROTTLE_ANON', '100/hour'),
        'user': environ.get('DRF_THROTTLE_USER', '1000/hour'),
        'login': environ.get('DRF_THROTTLE_LOGIN', '5/min'),
        'token-refresh': environ.get('DRF_THROTTLE_TOKEN_REFRESH', '30/min'),
        'signup': environ.get('DRF_THROTTLE_SIGNUP', '10/hour'),
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 110 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100
DATA_UPLOAD_MAX_NUMBER_FILES = 5

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'SIGNING_KEY': SECRET_KEY,
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

SPECTACULAR_SETTINGS = {
    'ENUM_NAME_OVERRIDES': {
        'PrinterNameEnum': 'back.apps.api.models.Printer.Name',
        'PrinterStatusEnum': 'back.apps.api.models.Printer.Status',
    },
}
