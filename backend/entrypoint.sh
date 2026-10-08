#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}..."
until python -c "
import socket, os, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((os.environ.get('POSTGRES_HOST', 'postgres'), int(os.environ.get('POSTGRES_PORT', 5432))))
    sys.exit(0)
except OSError:
    sys.exit(1)
"; do
  sleep 1
done
echo "PostgreSQL is up."

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
