from pathlib import Path
import os
import dj_database_url

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'change-this-secret-key-for-production'
)

DEBUG = os.environ.get(
    'DEBUG',
    'True'
).lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    '*'
).split(',')

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your Apps
    'core',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL Configuration
ROOT_URLCONF = 'gents_pos.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Custom Context Processor
                'core.context_processors.store_settings',
            ],
        },
    },
]

# WSGI
WSGI_APPLICATION = 'gents_pos.wsgi.application'

# PostgreSQL Database Configuration
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'gents_pos',
#         'USER': 'postgres',
#         'PASSWORD': 'admin123',
#         'HOST': 'localhost',
#         'PORT': '5433',
#     }
# }

# Password Validation
AUTH_PASSWORD_VALIDATORS = []

# Language and Time
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files
MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

# Default Primary Key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication Redirects
LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'dashboard'

LOGOUT_REDIRECT_URL = 'landing'
