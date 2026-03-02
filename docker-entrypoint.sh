#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -p 5432 -U geodjango; do
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Import shelters if database is empty
echo "Checking shelter data..."
python manage.py shell -c "
from shelter.models import Shelter
if Shelter.objects.count() == 0:
    print('No shelters found, importing data...')
    from django.core.management import call_command
    call_command('import_shelters')
else:
    print(f'Found {Shelter.objects.count()} shelters in database')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"