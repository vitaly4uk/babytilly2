"""
Django settings for babytilly2 project.

Generated by 'django-admin startproject' using Django 3.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path
from urllib.parse import urlparse

import environ
from kombu.utils.url import safequote

ADMINS = (("Vitaly Omelchuk", "vitaly.omelchuk@gmail.com"),)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


env = environ.Env(
    DEBUG=(bool, False),
    AWS_STORAGE_BUCKET_NAME=(str, "babytilly2"),
    AWS_DEFAULT_REGION=(str, "us-east-1"),
    REDIS_URL=(str, None),
)

EMAIL_BACKEND = "django_ses.SESBackend"
EMAIL_SUBJECT_PREFIX = "[b2b carrello] "
DEFAULT_FROM_EMAIL = "order.carrello@gmail.com"
SERVER_EMAIL = "order.carrello@gmail.com"
COMPLAINTS_EMAIL = "complaints.carrello@gmail.com"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    "babytilly2.apps.CarrelloConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "debug_toolbar",
    "mptt",
    "ckeditor",
    "ckeditor_uploader",
    "sorl.thumbnail",
    "bootstrap4",
    "fontawesomefree",
    "commercial",
    "celery",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "commercial.middleware.OrderMiddleware",
]

ROOT_URLCONF = "babytilly2.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "commercial.context_processors.root_sections",
            ],
        },
    },
]

WSGI_APPLICATION = "babytilly2.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": env.db_url(),
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = BASE_DIR / "static"


MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": env.cache_url(default="locmemcache://"),
}

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = env("AWS_DEFAULT_REGION")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_PRELOAD_METADATA = True
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_EXPIRE = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

LOGIN_URL = LOGOUT_URL = LOGIN_REDIRECT_URL = "/"

MPTT_ADMIN_LEVEL_INDENT = 30

THUMBNAIL_SIZE = {
    "small": "450",
    "cart_small": "90",
    "complaint": "200",
}
PAGINATOR = [10, 25, 50, 100]

if BROKER_URL := env("REDIS_URL"):
    CELERY_BROKER_URL = BROKER_URL
else:
    # aws_access_key = safequote(AWS_ACCESS_KEY_ID) if isinstance(AWS_ACCESS_KEY_ID, bytes) else AWS_ACCESS_KEY_ID
    # aws_secret_key = safequote(AWS_SECRET_ACCESS_KEY) if isinstance(AWS_SECRET_ACCESS_KEY, bytes) else AWS_SECRET_ACCESS_KEY
    CELERY_BROKER_URL = (
        f"sqs://{safequote(AWS_ACCESS_KEY_ID)}:{safequote(AWS_SECRET_ACCESS_KEY)}@"
    )
    CELERY_BROKER_TRANSPORT_OPTIONS = {
        "queue_name_prefix": "babytilly2-",
        "region": AWS_REGION_NAME,
        "visibility_timeout": 3600,
        "max_retries": 3,
        "polling_interval": 2,
        "wait_time_seconds": 10,
        "broker_connection_retry_on_startup": True,
    }
    CELERY_TASK_ALWAYS_EAGER = False

CKEDITOR_UPLOAD_PATH = "ckeditor_upload/"
CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline"],
            ["NumberedList", "BulletedList"],
            ["Link", "Unlink"],
            ["Format", "FontSize"],
            ["Blockquote"],
            ["Source", "-", "Image"],
        ],
        "allowedContent": True,
        "extraPlugins": ",".join(
            [
                "uploadimage",
            ]
        ),
    }
}


try:
    from local_settings import *
except ImportError:
    pass
