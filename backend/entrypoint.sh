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

exec "$@"
