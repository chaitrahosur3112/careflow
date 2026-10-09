#!/bin/sh
set -e

echo "Waiting for PostgreSQL database connection..."
until python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careflow_project.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
  sleep 1
done
echo "PostgreSQL is ready."

python manage.py migrate --noinput

# Create a default admin account for the viva demo if one doesn't exist yet.
# Credentials are read from env so nothing is hardcoded — see .env.example.
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if email and password and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(username='admin', email=email, password=password, role='ADMIN')
    print(f'Created superuser {email}')
"

exec "$@"
