"""
Improve WhatsApp error handling for users without phone numbers
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
from gigs.models import QuotationRequest, QuotationRequestProvider, Category
from whatsapp_service import get_whatsapp_service
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def add_whatsapp_fallback_logging():
    """Add better logging and fallback for WhatsApp failures"""
    
    improvements = '''
# Add to whatsapp_service.py for better error handling

def send_message_with_fallback(self, to: str, message: str, user_email: str = None) -> Dict[str, Any]:
    """
    Send WhatsApp message with fallback logging and user notification
    """
    if not to:
        error_msg = "No phone number provided for WhatsApp notification"
        logger.warning(f"WhatsApp skipped for user {user_email}: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'fallback_used': True,
            'user_notified': True
        }
    
    try:
        result = self.send_message(to, message)
        if result['success']:
            logger.info(f"WhatsApp sent successfully to {to} for user {user_email}")
        else:
            logger.error(f"WhatsApp failed for user {user_email}: {result.get('error')}")
        
        return result
        
    except Exception as e:
        error_msg = f"WhatsApp service error: {str(e)}"
        logger.error(f"WhatsApp error for user {user_email}: {error_msg}")
        
        # Could add email fallback here
        # send_email_fallback(user_email, message)
        
        return {
            'success': False,
            'error': error_msg,
            'fallback_used': True
        }
'''

    print("=== WhatsApp Service Improvements ===")
    print(improprovements)

def add_user_notification_for_missing_phone():
    """Add user notifications when phone numbers are missing"""
    
    notification_code = '''
# Add to gigs/views.py in create_quotation_request

# Enhanced WhatsApp notification with user feedback
if provider.phone:
    try:
        whatsapp_service = get_whatsapp_service()
        result = whatsapp_service.send_quotation_request(
            to=provider.phone,
            quotation_details=quotation_details
        )
        
        if result['success']:
            logger.info(f"WhatsApp notification sent to {provider.email}")
        else:
            logger.warning(f"WhatsApp failed for {provider.email}: {result.get('error')}")
            messages.info(request, f'WhatsApp notification could not be sent to {provider.email}. Please ensure they have a valid phone number.')
            
    except Exception as e:
        logger.error(f"WhatsApp notification error for {provider.email}: {e}")
        messages.warning(request, f'There was an issue sending WhatsApp notifications to some providers.')
else:
    # Log missing phone number
    logger.warning(f"Provider {provider.email} has no phone number - WhatsApp notification skipped")
    messages.info(request, f'Provider {provider.email} does not have a phone number. WhatsApp notifications were skipped.')
'''

    print("\n=== User Notification Improvements ===")
    print(notification_code)

def create_phone_number_reminder_system():
    """Create a system to remind users to add phone numbers"""
    
    reminder_code = '''
# Add to users/views.py or create a new management command

def check_users_without_phones():
    """Check and notify users without phone numbers"""
    users_without_phone = User.objects.filter(phone='', user_type='service_provider')
    
    for user in users_without_phone:
        # Send email reminder
        send_email_reminder(user)
        
        # Create notification in system
        from notifications.models import Notification
        Notification.objects.create(
            recipient=user,
            notification_type='phone_number_required',
            title='Phone Number Required for WhatsApp Notifications',
            notification_message='Please add your phone number to your profile to receive WhatsApp notifications for quotation requests.',
        )

def send_email_reminder(user):
    """Send email reminder to add phone number"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = 'Add Phone Number for WhatsApp Notifications'
    message = f'''
Dear {user.first_name or user.email},

To receive WhatsApp notifications for quotation requests and job opportunities, 
please add your phone number to your profile.

Visit: http://127.0.0.1:8000/users/profile/

Having a phone number will help you:
- Receive instant quotation requests
- Get price estimate confirmations
- Stay updated on job opportunities

Thank you!
'''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
'''

    print("\n=== Phone Number Reminder System ===")
    print(reminder_code)

def create_whatsapp_status_indicator():
    """Create a system to show WhatsApp status in user profiles"""
    
    status_code = '''
# Add to users/models.py

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Add WhatsApp status field
    whatsapp_verified = models.BooleanField(default=False, help_text="Whether WhatsApp number has been verified")
    whatsapp_last_notification = models.DateTimeField(null=True, blank=True)
    
    def get_whatsapp_status(self):
        """Get WhatsApp status for display"""
        if not self.user.phone:
            return "not_set"
        elif self.whatsapp_verified:
            return "verified"
        else:
            return "pending_verification"

# Add to user profile template
# Template code to show WhatsApp status
'''
<div class="whatsapp-status">
    {% if user.profile.get_whatsapp_status == "verified" %}
        <span class="badge bg-success">WhatsApp Verified</span>
    {% elif user.profile.get_whatsapp_status == "pending_verification" %}
        <span class="badge bg-warning">WhatsApp Pending</span>
    {% else %}
        <span class="badge bg-secondary">WhatsApp Not Set</span>
        <a href="{% url 'users:profile' %}" class="btn btn-sm btn-primary">Add Phone Number</a>
    {% endif %}
</div>
'''
'''

    print("\n=== WhatsApp Status Indicator ===")
    print(status_code)

def main():
    print("=== WhatsApp Error Handling Analysis ===")
    print()
    print("Current Status:")
    print("  + Phone validation exists in all views")
    print("  + WhatsApp errors are handled gracefully")
    print("  - No user feedback when WhatsApp fails")
    print("  - No reminders for missing phone numbers")
    print("  - No WhatsApp status indicators")
    print()
    
    add_whatsapp_fallback_logging()
    add_user_notification_for_missing_phone()
    create_phone_number_reminder_system()
    create_whatsapp_status_indicator()
    
    print("\n=== Implementation Priority ===")
    print("1. Add user notifications for missing phones (High)")
    print("2. Add better error logging (Medium)")
    print("3. Create phone number reminder system (Medium)")
    print("4. Add WhatsApp status indicators (Low)")

if __name__ == "__main__":
    main()
