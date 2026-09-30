from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile

PASSWORD = 'Eco@12345'
ACCOUNTS = [
    # username, full name, role, is_staff
    ('mc_officer', 'MC Officer', Profile.ROLE_OFFICER, True),
    ('collector1', 'Ramesh Collector', Profile.ROLE_COLLECTOR, False),
    ('collector2', 'Suresh Collector', Profile.ROLE_COLLECTOR, False),
    ('citizen1', 'Demo Citizen', Profile.ROLE_CITIZEN, False),
]


class Command(BaseCommand):
    help = "Create demo accounts (one MC officer, two collectors, one citizen) for testing."

    def handle(self, *args, **opts):
        for username, name, role, staff in ACCOUNTS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'first_name': name, 'email': f'{username}@example.com'})
            if created:
                user.set_password(PASSWORD)
            user.is_staff = staff
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role, profile.is_approved = role, True
            profile.phone = profile.phone or '9876543210'
            profile.city = profile.city or 'Kanpur'
            profile.state = profile.state or 'Uttar Pradesh'
            profile.pincode = profile.pincode or '208001'
            profile.save()
            self.stdout.write(f'{role:10} {username} ' + ('(created)' if created else '(updated)'))
        self.stdout.write(self.style.SUCCESS(f'Done. Password for new demo users: {PASSWORD}'))
