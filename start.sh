#!/bin/sh
# Start command for Render: prepare the database, then run gunicorn on the port Render gives us.
set -e
python manage.py migrate --noinput

# Make sure there is always an MC officer to log in with (only if the database has none).
python manage.py shell -c "
import os, sys
from django.contrib.auth.models import User
if User.objects.filter(is_staff=True).exists():
    sys.exit(0)
from django.core.management import call_command
u, p = os.environ.get('OFFICER_USER'), os.environ.get('OFFICER_PASSWORD')
if u and p:
    call_command('create_officer', u, p, '--name', 'MC Officer', '--city', 'Kanpur')
else:
    call_command('seed_demo')
"

# 512 MB RAM on the free plan: one worker, several threads.
exec gunicorn config.wsgi_prod:application \
  --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 120 \
  --access-logfile - --error-logfile -
