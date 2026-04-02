"""Signals for the accounts app.

Registered in AccountsConfig.ready() so they are loaded exactly once.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile row whenever a new User is created."""
    if created:
        from accounts.models import UserProfile
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Keep the UserProfile in sync when the User is saved.

    Uses get_or_create as a safety net in case the profile row is missing
    (e.g. for users created before signals were active).
    """
    from accounts.models import UserProfile
    UserProfile.objects.get_or_create(user=instance)
