from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Extra details + role for every account.

    citizen   - reports complaints / requests pickups
    collector - garbage collector who cleans approved tasks
    officer   - Municipal Corporation (MC) office staff who review everything
    """

    ROLE_CITIZEN = 'citizen'
    ROLE_COLLECTOR = 'collector'
    ROLE_OFFICER = 'officer'
    ROLE_CHOICES = [
        (ROLE_CITIZEN, 'Citizen'),
        (ROLE_COLLECTOR, 'Garbage Collector'),
        (ROLE_OFFICER, 'MC Officer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CITIZEN)
    phone = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    # Collector accounts must be approved by the MC office before they get work.
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
