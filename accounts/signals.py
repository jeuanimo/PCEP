"""Signals for the accounts app.

Registered in AccountsConfig.ready() so they are loaded exactly once.
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile row whenever a new User is created.

    Only runs on creation (``created=True``) so every subsequent User.save()
    incurs no extra query.  A get_or_create safety net in RegisterView handles
    the edge case of a user created before signals were active.
    """
    if created:
        from accounts.models import UserProfile
        UserProfile.objects.create(user=instance)
