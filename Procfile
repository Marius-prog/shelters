web: gunicorn geodjango.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --worker-class gthread --threads 4 --timeout 60 --graceful-timeout 30 --access-logfile - --error-logfile -
