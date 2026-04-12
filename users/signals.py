"""
Signals for syncing phone fields between User.phone and Profile.phone_number
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def sync_phone_number_from_user(sender, instance, created, **kwargs):
    """Sync User.phone to Profile.phone_number whenever User is saved"""
    if hasattr(instance, 'profile'):
        profile = instance.profile
        if instance.phone != profile.phone_number:
            profile.phone_number = instance.phone
            profile.save()
    else:
        # Create profile if it doesn't exist
        from .models import Profile
        profile, created = Profile.objects.get_or_create(user=instance)
        profile.phone_number = instance.phone
        profile.save()

@receiver(post_save, sender='users.Profile')
def sync_phone_number_from_profile(sender, instance, created, **kwargs):
    """Sync Profile.phone_number to User.phone whenever Profile is saved"""
    if hasattr(instance, 'user'):
        user = instance.user
        if instance.phone_number != user.phone:
            user.phone = instance.phone_number
            user.save()
