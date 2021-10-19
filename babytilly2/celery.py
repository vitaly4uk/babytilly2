import os

from celery import Celery
# set the default Django settings module for the 'celery' program.
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'babytilly2.settings')

app = Celery('babytilly2')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if settings.DEBUG:
    app.conf.CELERY_ALWAYS_EAGER = True
    app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
