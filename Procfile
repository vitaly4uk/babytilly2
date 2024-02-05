web: gunicorn babytilly2.wsgi --workers 1 --max-requests 600 --max-requests-jitter 10 --timeout 120 --capture-output --enable-stdio-inheritance --access-logfile -
worker: celery -A babytilly2 worker -c 1 --loglevel=INFO
release: python manage.py migrate --no-input
