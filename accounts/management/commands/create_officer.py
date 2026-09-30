from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Profile


class Command(BaseCommand):
    help = "Create (or promote) a Municipal Corporation officer account."

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('--email', default='')
        parser.add_argument('--name', default='')
        parser.add_argument('--city', default='')

    def handle(self, *args, **opts):
        username = opts['username']
        user = User.objects.filter(username=username).first()
        if user is None:
            if len(opts['password']) < 8:
                raise CommandError('Password must be at least 8 characters.')
            user = User.objects.create_user(username, opts['email'], opts['password'])
        user.first_name = opts['name'] or user.first_name
        user.is_staff = True
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = Profile.ROLE_OFFICER
        profile.is_approved = True
        profile.city = opts['city'] or profile.city
        profile.save()
        self.stdout.write(self.style.SUCCESS(f'Officer "{username}" is ready.'))
