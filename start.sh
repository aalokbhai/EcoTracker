#!/bin/sh
# Container entry point: prepare the database, then start gunicorn on the port the platform expects.
set -e
python manage.py migrate --noinput

# Make sure there is always an MC officer to log in with (first start / fresh disk).
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

exec gunicorn config.wsgi_prod:application \
  --bind 0.0.0.0:${PORT:-7860} --workers 2 --threads 4 --timeout 120 \
  --access-logfile - --error-logfile -
