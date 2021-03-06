"""
Django settings for addrsite project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

from __future__ import absolute_import, unicode_literals, print_function

import base64
import os
import platform
import sys


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# Ensure that we keep the secret key used in production secret!
_SECRET_KEY_FILE = os.path.join(BASE_DIR, '.secret-key')
with open(_SECRET_KEY_FILE) as fp:
    SECRET_KEY = fp.read().strip()


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


SERIALIZATION_MODULES = {
    "python_with_identity": 'addrreg.addreg_serializer'
}

TEST_RUNNER = 'addrreg.tests.util.TestRunner'

PROXIES = None
PUSH_URL = None
TESTING = False

# Application definition

INSTALLED_APPS = [
    'addrreg.apps.AddrRegConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.admindocs',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'admin_reorder',
]

if sys.platform == 'win32':
    INSTALLED_APPS += [
        'django_windows_tools',
    ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'admin_reorder.middleware.ModelAdminReorder',
]

ROOT_URLCONF = 'addrsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'addrsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Admin site reordering
# https://django-modeladmin-reorder.readthedocs.io/en/latest/readme.html#configuration

ADMIN_REORDER = (
    {'app': 'addrreg', 'models': (
        'addrreg.Address',
        'addrreg.BNumber',
        'addrreg.Road',
        'addrreg.District',
        'addrreg.Locality',
        'addrreg.Municipality',
        'addrreg.PostalCode',
        'addrreg.State',
    )},

    # Reorder app models
    {'app': 'auth', 'models': (
        'auth.User',
        'addrreg.MunicipalityRights',
    )},
)

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'da'

TIME_ZONE = 'Etc/UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, 'i18n')]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

LOCAL_STATIC_ROOT = os.path.join(BASE_DIR, 'addrsite', 'static')

STATICFILES_DIRS = [
    ('',  LOCAL_STATIC_ROOT),
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

if platform.python_implementation() == 'PyPy':
    from psycopg2cffi import compat
    compat.register()

if os.path.exists(os.path.join(os.path.dirname(__file__),
                               'local_settings.py')):
    from .local_settings import *  # noqa
else:
    print('No local settings!')


if sys.platform == 'win32':
    # this horrible hack injects the use of SSPI authentication into
    # django-sqlserver, fixing our authentication in Greenland
    import functools, sys

    from sqlserver import base
    from pytds import login

    orig_gcp = base.DatabaseWrapper.get_connection_params_pytds

    @functools.wraps(orig_gcp)
    def get_connection_params_pytds(self):
        """Returns a dict of parameters suitable for get_new_connection."""
        conn_params = orig_gcp(self)

        conn_params['auth'] = login.SspiAuth(
            user_name=conn_params['user'],
            password=conn_params['password'],
            server_name=conn_params['server'],
            port=conn_params['port'],
        )
   
        return conn_params

    base.DatabaseWrapper.get_connection_params_pytds = \
        get_connection_params_pytds
   

