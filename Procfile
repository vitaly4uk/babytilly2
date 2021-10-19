web: gunicorn babytilly2.wsgi --workers 2 --preload --max-requests 600 --max-requests-jitter 10 --timeout 120 --log-file -
worker: celery -A babytilly2 worker -B -l info
