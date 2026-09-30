from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Every new account (including createsuperuser) gets a profile."""
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={'role': Profile.ROLE_OFFICER if instance.is_staff else Profile.ROLE_CITIZEN},
        )
