from pathlib import Path

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
SECRET_KEY = '(_#sp@o945ou(eqd1tqjb31=ux8y9x%ecc3_us^-#6+$+335@l'

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
]

LOCAL_APPS = [
    'back',
    'back.apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

#################

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'