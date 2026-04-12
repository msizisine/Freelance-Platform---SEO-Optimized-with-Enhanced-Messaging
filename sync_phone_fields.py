"""
Sync phone fields between User.phone and Profile.phone_number
This ensures WhatsApp uses the phone number from the profile page
"""

import os
import sys
import django

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()

def sync_phone_fields():
    """Sync User.phone to Profile.phone_number for all users"""
    print("=== Syncing Phone Fields ===")
    print()
    
    updated_count = 0
    
    for user in User.objects.all():
        # Get or create profile
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Check if phone numbers are different
        user_phone = user.phone.strip() if user.phone else ""
        profile_phone = profile.phone_number.strip() if profile.phone_number else ""
        
        if user_phone != profile_phone:
            print(f"User: {user.email}")
            print(f"  User.phone: '{user_phone}'")
            print(f"  Profile.phone_number: '{profile_phone}'")
            
            # Update profile.phone_number with user.phone if user.phone is not empty
            if user_phone:
                profile.phone_number = user_phone
                profile.save()
                print(f"  -> Updated Profile.phone_number to: '{user_phone}'")
                updated_count += 1
            elif profile_phone and not user_phone:
                # Update user.phone with profile.phone_number if profile has phone but user doesn't
                user.phone = profile_phone
                user.save()
                print(f"  -> Updated User.phone to: '{profile_phone}'")
                updated_count += 1
            else:
                print(f"  -> Both fields are empty, no sync needed")
            
            print()
    
    print(f"Sync completed. Updated {updated_count} users.")

def create_phone_sync_signal():
    """Create a signal to automatically sync phone fields when user is updated"""
    signal_code = '''
# Add to users/models.py or create a new signals.py file

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def sync_phone_number(sender, instance, created, **kwargs):
    """Sync User.phone to Profile.phone_number whenever User is saved"""
    if hasattr(instance, 'profile'):
        profile = instance.profile
        if instance.phone != profile.phone_number:
            profile.phone_number = instance.phone
            profile.save()
    else:
        # Create profile if it doesn't exist
        from users.models import Profile
        profile, created = Profile.objects.get_or_create(user=instance)
        profile.phone_number = instance.phone
        profile.save()

@receiver(post_save, sender=Profile)
def sync_user_phone(sender, instance, created, **kwargs):
    """Sync Profile.phone_number to User.phone whenever Profile is saved"""
    if hasattr(instance, 'profile'):
        user = instance.user
        if instance.phone_number != user.phone:
            user.phone = instance.phone_number
            user.save()
'''
    
    print("=== Signal Code for Auto-Sync ===")
    print(signal_code)

def update_whatsapp_service_to_use_user_phone():
    """Update WhatsApp service to use User.phone instead of Profile.phone_number"""
    print("=== WhatsApp Service Update Required ===")
    print("To use the profile page phone field, update WhatsApp service to use:")
    print("user.phone instead of user.profile.phone_number")
    print()
    print("Changes needed in:")
    print("- whatsapp_service.py")
    print("- gigs/views.py") 
    print("- orders/views.py")
    print("- whatsapp_webhook.py")
    print()
    print("Replace:")
    print("user.profile.phone_number")
    print("With:")
    print("user.phone")

def main():
    sync_phone_fields()
    create_phone_sync_signal()
    update_whatsapp_service_to_use_user_phone()

if __name__ == "__main__":
    main()
