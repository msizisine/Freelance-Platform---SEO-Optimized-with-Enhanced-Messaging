"""
Fix phone number format for WhatsApp compatibility
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

User = get_user_model()

def fix_phone_number_format():
    """Fix phone numbers to be WhatsApp compatible"""
    print("=== Fixing Phone Number Format ===")
    
    # Get the provider with the problematic phone number
    provider = User.objects.get(email='msizi34@mobi-cafe.co.za')
    print(f"Current phone: '{provider.phone}'")
    
    # WhatsApp requires phone numbers in international format with +
    # South Africa country code is +27
    # The current number '0837009708' needs to be converted to '+2787009708'
    
    # Convert South African local format to international format
    if provider.phone.startswith('0'):
        # Remove leading 0 and add +27
        international_format = '+27' + provider.phone[1:]
        print(f"Converting to: '{international_format}'")
        
        # Update the phone number
        provider.phone = international_format
        provider.save()
        
        # Also update profile phone number
        if hasattr(provider, 'profile'):
            provider.profile.phone_number = international_format
            provider.profile.save()
        
        print("Phone number updated successfully!")
        
        # Test WhatsApp with the new format
        from whatsapp_service import get_whatsapp_service
        whatsapp_service = get_whatsapp_service()
        
        test_result = whatsapp_service.send_message(
            to=international_format,
            message="Test message with corrected phone format"
        )
        
        print(f"WhatsApp test result: {test_result}")
        
    else:
        print("Phone number doesn't start with '0' - manual conversion needed")

def check_all_phone_formats():
    """Check all phone numbers in the system"""
    print("\n=== Checking All Phone Formats ===")
    
    for user in User.objects.all():
        if user.phone:
            print(f"{user.email}: '{user.phone}'")
            
            # Check if format is correct for WhatsApp
            if user.phone.startswith('+'):
                print(f"  -> International format (good)")
            elif user.phone.startswith('0'):
                print(f"  -> Local format (needs conversion)")
            else:
                print(f"  -> Unknown format")

def fix_other_phones():
    """Fix other phone numbers that need conversion"""
    print("\n=== Fixing Other Phone Numbers ===")
    
    # Fix msizi32's phone number
    msizi32 = User.objects.get(email='msizi32@mobi-cafe.co.za')
    if msizi32.phone and msizi32.phone.startswith('0'):
        international_format = '+27' + msizi32.phone[1:]
        print(f"Fixing {msizi32.email}: '{msizi32.phone}' -> '{international_format}'")
        
        msizi32.phone = international_format
        msizi32.save()
        
        if hasattr(msizi32, 'profile'):
            msizi32.profile.phone_number = international_format
            msizi32.profile.save()
        
        print("Fixed successfully!")

def main():
    fix_phone_number_format()
    fix_other_phones()
    check_all_phone_formats()

if __name__ == "__main__":
    main()
