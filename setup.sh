#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

# Migrate database
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin');
    print('Superuser created.');
else:
    print('Superuser already exists.');"

# Create default roles
echo "Creating default roles..."
python manage.py shell -c "
from users.models import Role;
roles = ['Admin', 'Doctor', 'Patient', 'Staff'];
for role_name in roles:
    Role.objects.get_or_create(name=role_name, description=f'{role_name} role');
    print(f'Role {role_name} created or found.');
"

echo "Setup completed!"
echo "Run 'source venv/bin/activate && python manage.py runserver' to start the server"