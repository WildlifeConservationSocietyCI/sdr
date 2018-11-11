"""
Django settings for app project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys

# Options: None, DEV, PROD
ENVIRONMENT = os.environ.get('ENV')
if ENVIRONMENT:
    ENVIRONMENT = ENVIRONMENT.lower()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+d_@vl55=26qzea1x&@es70=&sfmrtkgtsdou-7mgj^b4f57+#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ENVIRONMENT not in ('master',)

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS').split(',')]
if DEBUG:
    ALLOWED_HOSTS = ['*']
    # INTERNAL_IPS = ['172.19.0.1']

    from fnmatch import fnmatch

    class glob_list(list):
        def __contains__(self, key):
            for elt in self:
                if fnmatch(key, elt):
                    return True
            return False

    INTERNAL_IPS = glob_list(['127.0.0.1', '172.*.*.*'])

ADMINS = [('Administrator', admin.strip()) for admin in os.environ['ADMINS'].split(',')]


# Application definition

INSTALLED_APPS = [
    'app.apps.SuitConfig',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_extensions',
    'storages',
    'django_cleanup',
    'base',
    'sdr',
    'pn',
    'species',
    'muirweb',
    'tools',
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME') or 'sdr',
        'USER': os.environ.get('DB_USER') or 'postgres',
        'PASSWORD': os.environ.get('DB_PASSWORD') or 'postgres',
        'HOST': os.environ.get('DB_HOST') or 'localhost',
        'PORT': os.environ.get('DB_PORT') or '5432',
        'OPTIONS': {
            'sslmode': os.environ['VM_DB_SSL'] if 'VM_DB_SSL' in os.environ else 'disable',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Admin customization

PROJECT_NAME = os.environ.get('PROJECT_NAME', 'SDR').strip('"')
QA_GROUP_NAME = os.environ.get('QA_GROUP_NAME', 'administrators')
ZOTERO_GROUP = os.environ.get('ZOTERO_GROUP')
DEFAULT_LAT = os.environ.get('DEFAULT_LAT')  # 4972357
DEFAULT_LON = os.environ.get('DEFAULT_LON')  # -8229861
DEFAULT_ZOOM = os.environ.get('DEFAULT_ZOOM')  # 10
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION')
AWS_BACKUP_BUCKET = os.environ.get('AWS_BACKUP_BUCKET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
COL_URL = 'http://webservice.catalogueoflife.org/col/webservice'

# email
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USE_TLS = True

# Static files (CSS, JavaScript, Images) and media files
# https://docs.djangoproject.com/en/1.11/howto/static-files/
# https://docs.djangoproject.com/en/1.11/topics/files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = 'app.utils.OverwriteFileSystemStorage'
MEDIA_URL = '/media/'
if ENVIRONMENT in ('master',):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = '//%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, 'media')

DEBUG_LEVEL = 'ERROR'
if ENVIRONMENT in ('local', 'dev'):
    DEBUG_LEVEL = 'DEBUG'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': DEBUG_LEVEL,
            'class': 'logging.StreamHandler',
            'stream': sys.stdout
        }
    },
    'formatters': {
        'file': {
            'format': '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}
