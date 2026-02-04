release: python manage.py migrate --no-input
web: gunicorn panacare.wsgi --bind 0.0.0.0:$PORT
