#!/bin/bash
set -e

echo "Starting Panacare Healthcare Backend..."

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."

    max_tries=30
    count=0

    until python << END
import sys
import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'panacare_db'),
        user=os.environ.get('DB_USER', 'panacare'),
        password=os.environ.get('DB_PASSWORD', 'panacare'),
        host=os.environ.get('DB_HOST', 'db'),
        port=os.environ.get('DB_PORT', '5432')
    )
    conn.close()
    sys.exit(0)
except psycopg2.OperationalError:
    sys.exit(1)
END
    do
        count=$((count+1))
        if [ $count -ge $max_tries ]; then
            echo "PostgreSQL did not become ready in time"
            exit 1
        fi
        echo "PostgreSQL is unavailable - sleeping (attempt $count/$max_tries)"
        sleep 1
    done

    echo "PostgreSQL is ready!"
}

# Wait for database
wait_for_postgres

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (optional for development, uncomment if needed)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional)
# Uncomment and modify as needed
# echo "Checking for superuser..."
# python manage.py shell << END
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'admin')
#     print('Superuser created.')
# else:
#     print('Superuser already exists.')
# END

echo "Starting Django development server..."
exec "$@"
