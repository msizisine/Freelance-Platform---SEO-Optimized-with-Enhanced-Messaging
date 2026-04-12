"""
Phone Number Status Classification and Handling System
Manages different phone number states and provides appropriate handling strategies
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import Notification

# Try to import phone utils, but make it optional
try:
    from phone_utils import validate_phone_number, format_for_whatsapp
    PHONE_UTILS_AVAILABLE = True
except ImportError:
    PHONE_UTILS_AVAILABLE = False
    print("Warning: Phone utils not available in phone_status_system. Phone validation will be disabled.")
    
    # Create dummy functions if phone_utils is not available
    def validate_phone_number(value):
        return True, value, None  # is_valid, formatted, error
    
    def format_for_whatsapp(value):
        return value

logger = logging.getLogger(__name__)

class PhoneStatus(Enum):
    """Phone number status classification"""
    VALID = "valid"
    MISSING = "missing"
    INVALID = "invalid"
    UNVERIFIED = "unverified"

class PhoneStatusSystem:
    """System for managing phone number status and handling"""
    
    @classmethod
    def get_phone_status(cls, user) -> Tuple[PhoneStatus, str]:
        """
        Get the phone status for a user
        
        Args:
            user: User object
            
        Returns:
            Tuple of (PhoneStatus, message)
        """
        if not user.phone:
            return PhoneStatus.MISSING, "No phone number provided"
        
        # Validate the phone number
        is_valid, formatted, error = validate_phone_number(user.phone)
        
        if is_valid:
            # Check if the number was recently updated (unverified)
            if hasattr(user, 'profile') and user.profile.phone_number != formatted:
                return PhoneStatus.UNVERIFIED, f"Phone number updated to {formatted}"
            return PhoneStatus.VALID, f"Valid phone number: {formatted}"
        else:
            return PhoneStatus.INVALID, f"Invalid phone number: {error}"
    
    @classmethod
    def get_all_users_by_status(cls) -> Dict[PhoneStatus, List]:
        """
        Get all users grouped by phone status
        
        Returns:
            Dictionary with PhoneStatus as keys and user lists as values
        """
        User = get_user_model()
        users_by_status = {
            PhoneStatus.VALID: [],
            PhoneStatus.MISSING: [],
            PhoneStatus.INVALID: [],
            PhoneStatus.UNVERIFIED: []
        }
        
        for user in User.objects.all():
            status, message = cls.get_phone_status(user)
            users_by_status[status].append({
                'user': user,
                'status': status.value,
                'message': message
            })
        
        return users_by_status
    
    @classmethod
    def handle_missing_phone(cls, user, context: str = "general") -> Dict[str, any]:
        """
        Handle users with missing phone numbers
        
        Args:
            user: User object
            context: Context where this was triggered (quotation, job_application, etc.)
            
        Returns:
            Dict with handling result
        """
        logger.info(f"Handling missing phone for {user.email} in context: {context}")
        
        # Create notification for user
        notification_message = cls._get_missing_phone_message(context)
        
        try:
            Notification.objects.create(
                recipient=user,
                notification_type='phone_number_required',
                title='Phone Number Required',
                notification_message=notification_message,
            )
        except Exception as e:
            logger.error(f"Failed to create notification for {user.email}: {e}")
        
        # Send email if available
        if user.email:
            cls._send_phone_reminder_email(user, context)
        
        return {
            'status': 'handled',
            'action': 'notification_sent',
            'message': 'User notified about missing phone number',
            'fallback_available': False
        }
    
    @classmethod
    def handle_invalid_phone(cls, user, error_message: str, context: str = "general") -> Dict[str, any]:
        """
        Handle users with invalid phone numbers
        
        Args:
            user: User object
            error_message: Specific validation error
            context: Context where this was triggered
            
        Returns:
            Dict with handling result
        """
        logger.info(f"Handling invalid phone for {user.email}: {error_message}")
        
        # Create notification for user with specific guidance
        notification_message = cls._get_invalid_phone_message(error_message, context)
        
        try:
            Notification.objects.create(
                recipient=user,
                notification_type='phone_number_invalid',
                title='Invalid Phone Number',
                notification_message=notification_message,
            )
        except Exception as e:
            logger.error(f"Failed to create notification for {user.email}: {e}")
        
        # Send email with detailed guidance
        if user.email:
            cls._send_invalid_phone_email(user, error_message, context)
        
        return {
            'status': 'handled',
            'action': 'notification_sent',
            'message': 'User notified about invalid phone number',
            'fallback_available': False
        }
    
    @classmethod
    def handle_notification_failure(cls, user, service: str, error: str, context: str) -> Dict[str, any]:
        """
        Handle notification failures (WhatsApp/SMS)
        
        Args:
            user: User object
            service: Service that failed (whatsapp, sms)
            error: Error message
            context: Context where this was triggered
            
        Returns:
            Dict with handling result
        """
        logger.warning(f"Notification failed for {user.email}: {service} - {error}")
        
        # Create notification about the failure
        notification_message = cls._get_notification_failure_message(service, error, context)
        
        try:
            Notification.objects.create(
                recipient=user,
                notification_type='notification_failed',
                title=f'{service.title()} Notification Failed',
                notification_message=notification_message,
            )
        except Exception as e:
            logger.error(f"Failed to create failure notification for {user.email}: {e}")
        
        # Try email fallback for critical notifications
        if context in ['quotation_request', 'payment_confirmation', 'job_application']:
            cls._send_email_fallback(user, context)
        
        return {
            'status': 'handled',
            'action': 'email_fallback_attempted',
            'message': f'Email fallback attempted for {context}',
            'fallback_available': True
        }
    
    @classmethod
    def _get_missing_phone_message(cls, context: str) -> str:
        """Get message for missing phone number notification"""
        messages = {
            'quotation_request': 'To receive WhatsApp notifications for new quotation requests, please add your phone number to your profile. Service providers need phone numbers to respond quickly to opportunities.',
            'job_application': 'To receive WhatsApp notifications about your job applications, please add your phone number to your profile. Homeowners prefer to contact providers directly.',
            'payment_confirmation': 'To receive WhatsApp payment confirmations, please add your phone number to your profile for instant payment notifications.',
            'general': 'Please add your phone number to your profile to receive WhatsApp notifications and updates. This helps you stay connected with opportunities and important updates.'
        }
        return messages.get(context, messages['general'])
    
    @classmethod
    def _get_invalid_phone_message(cls, error: str, context: str) -> str:
        """Get message for invalid phone number notification"""
        base_message = f'There is an issue with your phone number: {error}. Please update your profile with a valid South African phone number (e.g., 0837009708).'
        
        context_specific = {
            'quotation_request': ' This is preventing you from receiving WhatsApp notifications about new quotation requests.',
            'job_application': ' This is preventing homeowners from contacting you about job applications.',
            'payment_confirmation': ' This is preventing you from receiving instant payment confirmations.',
            'general': ' This is preventing you from receiving WhatsApp notifications.'
        }
        
        return base_message + context_specific.get(context, context_specific['general'])
    
    @classmethod
    def _get_notification_failure_message(cls, service: str, error: str, context: str) -> str:
        """Get message for notification failure"""
        return f'Your {service} notification could not be sent: {error}. We have sent you this notification via email instead. Please check your email for important updates about {context}.'
    
    @classmethod
    def _send_phone_reminder_email(cls, user, context: str):
        """Send email reminder for missing phone number"""
        subject = 'Add Phone Number for WhatsApp Notifications'
        message = f'''
Dear {user.first_name or user.email},

To receive WhatsApp notifications and stay connected with opportunities, please add your phone number to your profile.

Why add your phone number?
- Receive instant quotation requests
- Get job application notifications  
- Payment confirmations
- Important platform updates

Update your profile here: http://127.0.0.1:8000/users/profile/

Enter your phone number in format: 0837009708 (South African numbers)

Thank you!
The Freelance Platform Team
'''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Phone reminder email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send phone reminder email to {user.email}: {e}")
    
    @classmethod
    def _send_invalid_phone_email(cls, user, error: str, context: str):
        """Send email for invalid phone number"""
        subject = 'Invalid Phone Number - Please Update Your Profile'
        message = f'''
Dear {user.first_name or user.email},

There is an issue with the phone number in your profile: {error}

Please update your profile with a valid South African phone number:
- Format: 0837009708 (starts with 0, followed by 9 digits)
- Examples: 0837009708, 0712345678, 0612345678

Update your profile here: http://127.0.0.1:8000/users/profile/

This is preventing you from receiving WhatsApp notifications for {context}.

Thank you!
The Freelance Platform Team
'''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Invalid phone email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send invalid phone email to {user.email}: {e}")
    
    @classmethod
    def _send_email_fallback(cls, user, context: str):
        """Send email fallback for critical notifications"""
        subject = f'Important Update: {context.replace("_", " ").title()}'
        message = f'''
Dear {user.first_name or user.email},

We were unable to send you a WhatsApp notification about: {context}

Please log in to your dashboard to check for important updates:
http://127.0.0.1:8000/dashboard/

To receive instant WhatsApp notifications in the future, please ensure your phone number is correctly set in your profile.

Thank you!
The Freelance Platform Team
'''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Email fallback sent to {user.email} for {context}")
        except Exception as e:
            logger.error(f"Failed to send email fallback to {user.email}: {e}")

# Convenience functions
def get_user_phone_status(user) -> Tuple[PhoneStatus, str]:
    """Get phone status for a user"""
    return PhoneStatusSystem.get_phone_status(user)

def handle_phone_issue(user, status: PhoneStatus, error: str = None, context: str = "general") -> Dict[str, any]:
    """Handle phone number issues"""
    if status == PhoneStatus.MISSING:
        return PhoneStatusSystem.handle_missing_phone(user, context)
    elif status == PhoneStatus.INVALID:
        return PhoneStatusSystem.handle_invalid_phone(user, error or "Invalid format", context)
    else:
        return {'status': 'no_action_needed', 'message': 'Phone number is valid'}

def get_phone_status_dashboard():
    """Get phone status dashboard data"""
    return PhoneStatusSystem.get_all_users_by_status()
