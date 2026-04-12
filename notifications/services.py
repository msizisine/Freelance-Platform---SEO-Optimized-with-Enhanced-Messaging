import random
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import (
    Notification, NotificationTemplate, OTPCode, 
    CommunicationLog, SMSMessage, WhatsAppMessage,
    NotificationPreference
)


class NotificationService:
    """Central service for managing all notifications"""
    
    @staticmethod
    def send_notification(recipient, notification_type, title, notification_message, 
                        sender=None, channels=None, gig=None, order=None, 
                        review=None, conversation=None, context=None):
        """
        Send notification through multiple channels
        
        Args:
            recipient: User object who will receive the notification
            notification_type: Type of notification (from Notification.NOTIFICATION_TYPES)
            title: Notification title
            message: Notification message
            sender: User object who sent the notification (optional)
            channels: List of channels to send through (optional)
            gig: Related gig object (optional)
            order: Related order object (optional)
            review: Related review object (optional)
            conversation: Related conversation object (optional)
            context: Additional context for templates (optional)
        """
        
        # Get user preferences for this notification type
        preferences = NotificationService.get_user_preferences(recipient, notification_type)
        
        # Determine channels to use
        if channels is None:
            channels = []
            if preferences.email_enabled:
                channels.append('email')
            if preferences.sms_enabled and recipient.phone:
                channels.append('sms')
            if preferences.whatsapp_enabled and recipient.phone:
                channels.append('whatsapp')
            if preferences.in_app_enabled:
                channels.append('in_app')
        
        # Create notification record
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=notification_message,
            channels=','.join(channels) if channels else 'in_app',
            gig=gig,
            order=order,
            review=review,
            conversation=conversation
        )
        
        # Auto-create conversation messages for important events
        NotificationService._create_conversation_message_if_needed(
            notification, recipient, sender, notification_type, title, notification_message,
            gig, order, context
        )
        
        # Send through each channel
        for channel in channels:
            try:
                NotificationService._send_via_channel(
                    notification, channel, recipient, context or {}
                )
            except Exception as e:
                CommunicationLog.objects.create(
                    notification=notification,
                    channel=channel,
                    status='failed',
                    error_message=str(e)
                )
        
        return notification
    
    @staticmethod
    def _create_conversation_message_if_needed(notification, recipient, sender, notification_type, title, notification_message, gig, order, context):
        """Create conversation messages for important events like hiring and responses"""
        
        # Define which notification types should create conversation messages
        message_types = ['job_applied', 'job_accepted', 'job_completed', 'job_rejected', 'quotation_response']
        
        if notification_type not in message_types:
            return
        
        try:
            from messaging.models import Conversation, Message
            
            # Find or create conversation between sender and recipient
            conversation = None
            
            # Try to find existing conversation
            existing_conversations = Conversation.objects.filter(participants__in=[sender, recipient]).distinct()
            for conv in existing_conversations:
                participants = conv.participants.all()
                if sender in participants and recipient in participants:
                    conversation = conv
                    break
            
            # Create new conversation if doesn't exist
            if not conversation and sender:
                conversation = Conversation.objects.create()
                conversation.participants.add(sender, recipient)
            
            if conversation:
                # Create message content based on notification type
                message_content = NotificationService._get_message_content(notification_type, title, notification_message, gig, order, context)
                
                # Create the message
                Message.objects.create(
                    conversation=conversation,
                    sender=sender or notification.recipient,  # Use system user if no sender
                    content=message_content,
                    is_read=False
                )
                
        except Exception as e:
            # Log error but don't fail the notification
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create conversation message for notification {notification.id}: {e}")
    
    @staticmethod
    def _get_message_content(notification_type, title, notification_message, gig, order, context):
        """Generate appropriate message content based on notification type"""
        
        if notification_type == 'job_applied':
            return f"<strong>{title}</strong><br><br>{notification_message}<br><br><em>This is an automated message about your job posting.</em>"
        elif notification_type == 'job_accepted':
            return f"<strong>{title}</strong><br><br>{notification_message}<br><br><em>Congratulations! Your application was accepted.</em>"
        elif notification_type == 'job_completed':
            return f"<strong>{title}</strong><br><br>{notification_message}<br><br><em>The job has been marked as completed.</em>"
        elif notification_type == 'job_rejected':
            return f"<strong>{title}</strong><br><br>{notification_message}<br><br><em>Your application was not selected for this job.</em>"
        elif notification_type == 'quotation_response':
            return f"<strong>{title}</strong><br><br>{notification_message}<br><br><em>A response to your quotation request has been received.</em>"
        else:
            return f"<strong>{title}</strong><br><br>{notification_message}"
    
    @staticmethod
    def _send_via_channel(notification, channel, recipient, context):
        """Send notification through specific channel"""
        
        # Get template for this notification type
        try:
            template = NotificationTemplate.objects.get(
                notification_type=notification.notification_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            # Use default message if no template
            template_content = notification.message
            subject = notification.title
        else:
            template_content = getattr(template, f'{channel}_template') or notification.message
            subject = template.subject_template or notification.title
        
        # Render template with context
        context.update({
            'user': recipient,
            'notification': notification,
            'title': notification.title,
            'message': notification.message,
        })
        
        if channel == 'email':
            EmailService.send_email(
                recipient.email,
                subject,
                template_content,
                context,
                notification
            )
        elif channel == 'sms':
            SMSService.send_sms(
                recipient.phone,
                template_content,
                context,
                notification
            )
        elif channel == 'whatsapp':
            WhatsAppService.send_whatsapp(
                recipient.phone,
                template_content,
                context,
                notification
            )
        elif channel == 'in_app':
            # In-app notifications are already created in the database
            pass
    
    @staticmethod
    def get_user_preferences(user, notification_type):
        """Get user preferences for a specific notification type"""
        try:
            return NotificationPreference.objects.get(
                user=user,
                notification_type=notification_type
            )
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            defaults = {
                'email_enabled': True,
                'sms_enabled': False,
                'whatsapp_enabled': False,
                'in_app_enabled': True,
                'push_enabled': False,
            }
            
            # Enable SMS/WhatsApp for critical notifications
            critical_notifications = ['otp_login', 'password_reset', 'job_accepted']
            if notification_type in critical_notifications:
                defaults['sms_enabled'] = True
                defaults['whatsapp_enabled'] = True
            
            preference = NotificationPreference.objects.create(
                user=user,
                notification_type=notification_type,
                **defaults
            )
            return preference
    
    @staticmethod
    def create_default_templates():
        """Create default notification templates"""
        templates = {
            'job_applied': {
                'subject_template': 'New Job Application - {gig.title}',
                'email_template': '''
                    <p>Hi {user.first_name},</p>
                    <p>You have a new job application for: <strong>{gig.title}</strong></p>
                    <p>Applicant: {sender.first_name} {sender.last_name}</p>
                    <p>Message: {message}</p>
                    <p><a href="{site_url}/gigs/{gig.id}/">View Job Details</a></p>
                ''',
                'sms_template': 'New application for {gig.title}. Applicant: {sender.first_name}. View at {site_url}/gigs/{gig.id}/',
                'whatsapp_template': '📋 *New Job Application*\n\n*Job:* {gig.title}\n*Applicant:* {sender.first_name} {sender.last_name}\n\nView details: {site_url}/gigs/{gig.id}/',
                'in_app_template': 'New application for {gig.title} from {sender.first_name} {sender.last_name}',
            },
            'job_accepted': {
                'subject_template': 'Job Application Accepted - {gig.title}',
                'email_template': '''
                    <p>Congratulations {user.first_name}!</p>
                    <p>Your application for <strong>{gig.title}</strong> has been accepted!</p>
                    <p>Client: {sender.first_name} {sender.last_name}</p>
                    <p><a href="{site_url}/gigs/{gig.id}/">View Job Details</a></p>
                    <p>Reply ACCEPT to confirm via SMS or WhatsApp</p>
                ''',
                'sms_template': '🎉 Your application for {gig.title} was accepted! Reply ACCEPT to confirm. View: {site_url}/gigs/{gig.id}/',
                'whatsapp_template': '🎉 *Application Accepted!*\n\n*Job:* {gig.title}\n*Client:* {sender.first_name} {sender.last_name}\n\nReply ACCEPT to confirm this job.\n\nView: {site_url}/gigs/{gig.id}/',
                'in_app_template': 'Your application for {gig.title} has been accepted! Reply ACCEPT to confirm.',
            },
            'job_completed': {
                'subject_template': 'Job Completed - {gig.title}',
                'email_template': '''
                    <p>Hi {user.first_name},</p>
                    <p>The job <strong>{gig.title}</strong> has been marked as completed.</p>
                    <p>Please leave a review for the service provider.</p>
                    <p><a href="{site_url}/reviews/create/{order.id}/">Leave Review</a></p>
                ''',
                'sms_template': 'Job {gig.title} completed. Please leave a review: {site_url}/reviews/create/{order.id}/',
                'whatsapp_template': '✅ *Job Completed*\n\n*Job:* {gig.title}\n\nPlease leave a review:\n{site_url}/reviews/create/{order.id}/',
                'in_app_template': 'Job {gig.title} completed. Please leave a review.',
            },
            'provider_verified': {
                'subject_template': 'You are now a Verified Service Provider!',
                'email_template': '''
                    <p>Congratulations {user.first_name}!</p>
                    <p>Your service provider account has been verified by our admin team.</p>
                    <p>You now have a verified badge on your profile and increased visibility.</p>
                    <p><a href="{site_url}/">View Your Profile</a></p>
                ''',
                'sms_template': '🏆 Congratulations! Your service provider account is now VERIFIED. View your profile: {site_url}/',
                'whatsapp_template': '🏆 *Account Verified!*\n\nCongratulations {user.first_name}! Your service provider account is now verified.\n\nView your profile: {site_url}/',
                'in_app_template': 'Your service provider account has been verified! You now have a verified badge.',
            },
            'otp_login': {
                'subject_template': 'Your Login Code',
                'email_template': '''
                    <p>Hi {user.first_name},</p>
                    <p>Your login code is: <strong>{otp_code}</strong></p>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this, please ignore this message.</p>
                ''',
                'sms_template': 'Your login code is: {otp_code}. Valid for 10 minutes.',
                'whatsapp_template': '🔐 *Login Code*\n\nYour login code is: *{otp_code}*\n\nValid for 10 minutes.',
                'in_app_template': 'Your login code is: {otp_code}',
            },
        }
        
        for notification_type, data in templates.items():
            NotificationTemplate.objects.get_or_create(
                notification_type=notification_type,
                defaults=data
            )


class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_email(to_email, subject, template_content, context, notification=None):
        """Send email notification"""
        try:
            # Render template
            if '{' in template_content:
                message = render_to_string('notifications/email_template.html', {
                    'subject': subject,
                    'content': template_content.format(**context),
                    'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                    **context
                })
            else:
                message = template_content
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@freelanceplatform.com'),
                recipient_list=[to_email],
                html_message=message if '<' in message else None,
                fail_silently=False
            )
            
            # Log success
            if notification:
                CommunicationLog.objects.create(
                    notification=notification,
                    channel='email',
                    status='sent'
                )
            
            return True
            
        except Exception as e:
            # Log error
            if notification:
                CommunicationLog.objects.create(
                    notification=notification,
                    channel='email',
                    status='failed',
                    error_message=str(e)
                )
            raise e


class SMSService:
    """Service for sending SMS notifications"""
    
    @staticmethod
    def send_sms(to_phone, message, context, notification=None):
        """Send SMS notification"""
        try:
            # Format message with context
            if '{' in message:
                formatted_message = message.format(**context)
            else:
                formatted_message = message
            
            # Create SMS record
            sms = SMSMessage.objects.create(
                recipient=to_phone,
                message=formatted_message,
                notification=notification
            )
            
            # Send via provider (Twilio example)
            if getattr(settings, 'TWILIO_ENABLED', False):
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                message = client.messages.create(
                    body=formatted_message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=to_phone
                )
                
                sms.external_id = message.sid
                sms.status = 'sent'
                sms.sent_at = timezone.now()
                sms.save()
                
                # Log success
                if notification:
                    CommunicationLog.objects.create(
                        notification=notification,
                        channel='sms',
                        status='sent',
                        external_id=message.sid
                    )
            else:
                # Mock for development
                sms.status = 'sent'
                sms.sent_at = timezone.now()
                sms.save()
                
                if notification:
                    CommunicationLog.objects.create(
                        notification=notification,
                        channel='sms',
                        status='sent'
                    )
            
            return True
            
        except Exception as e:
            # Log error
            if notification:
                CommunicationLog.objects.create(
                    notification=notification,
                    channel='sms',
                    status='failed',
                    error_message=str(e)
                )
            raise e


class WhatsAppService:
    """Service for sending WhatsApp notifications"""
    
    @staticmethod
    def send_whatsapp(to_phone, message, context, notification=None):
        """Send WhatsApp message using configured provider"""
        try:
            from .whatsapp_providers import WhatsAppProviderFactory
            if '{' in message and context:
                try:
                    formatted_message = message.format(**context)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Template formatting failed: {e}")
                    formatted_message = message
            else:
                formatted_message = message
            
            # Create WhatsApp record
            whatsapp = WhatsAppMessage.objects.create(
                recipient=to_phone,
                message=formatted_message,
                notification=notification
            )
            
            # Send via provider (Twilio WhatsApp example)
            if getattr(settings, 'TWILIO_WHATSAPP_ENABLED', False):
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                # Check if we have content template information
                content_sid = context.get('content_sid')
                content_variables = context.get('content_variables')
                
                if content_sid:
                    # Use content template
                    message = client.messages.create(
                        from_=f'whatsapp:{settings.TWILIO_PHONE_NUMBER}',
                        content_sid=content_sid,
                        content_variables=content_variables or '{}',
                        to=f'whatsapp:{to_phone}'
                    )
                else:
                    # Use regular message body
                    message = client.messages.create(
                        body=formatted_message,
                        from_=f'whatsapp:{settings.TWILIO_PHONE_NUMBER}',
                        to=f'whatsapp:{to_phone}'
                    )
                
                whatsapp.external_id = message.sid
                whatsapp.status = 'sent'
                whatsapp.sent_at = timezone.now()
                whatsapp.save()
                
                # Log success
                if notification:
                    CommunicationLog.objects.create(
                        notification=notification,
                        channel='whatsapp',
                        status='sent',
                        external_id=message.sid
                    )
            else:
                # Mock for development
                whatsapp.status = 'sent'
                whatsapp.sent_at = timezone.now()
                whatsapp.save()
                
                if notification:
                    CommunicationLog.objects.create(
                        notification=notification,
                        channel='whatsapp',
                        status='sent'
                    )
            
            return True
            
        except Exception as e:
            # Log error
            if notification:
                CommunicationLog.objects.create(
                    notification=notification,
                    channel='whatsapp',
                    status='failed',
                    error_message=str(e)
                )
            raise e


class OTPService:
    """Service for managing OTP codes"""
    
    @staticmethod
    def generate_otp(user, phone_number, channel='sms', purpose='login'):
        """Generate and send OTP code"""
        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiry (10 minutes from now)
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Create OTP record
        otp = OTPCode.objects.create(
            user=user,
            code=code,
            phone_number=phone_number,
            channel=channel,
            purpose=purpose,
            expires_at=expires_at
        )
        
        # Send OTP via selected channel
        if channel == 'sms':
            SMSService.send_sms(
                phone_number,
                'Your verification code is: {otp_code}. Valid for 10 minutes.',
                {'otp_code': code}
            )
        elif channel == 'whatsapp':
            WhatsAppService.send_whatsapp(
                phone_number,
                '🔐 *Verification Code*\n\nYour code is: *{otp_code}*\n\nValid for 10 minutes.',
                {'otp_code': code}
            )
        
        return otp
    
    @staticmethod
    def verify_otp(user, code, purpose='login'):
        """Verify OTP code"""
        try:
            otp = OTPCode.objects.get(
                user=user,
                code=code,
                purpose=purpose,
                is_used=False
            )
            
            if not otp.is_valid():
                return False
            
            # Mark as used
            otp.mark_as_used()
            return True
            
        except OTPCode.DoesNotExist:
            return False
    
    @staticmethod
    def handle_sms_response(phone_number, message):
        """Handle incoming SMS responses for job acceptance"""
        message = message.strip().upper()
        
        # Look for recent job acceptance notifications
        recent_notifications = Notification.objects.filter(
            recipient__phone=phone_number,
            notification_type='job_accepted',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-created_at').first()
        
        if not recent_notifications:
            return {'status': 'error', 'message': 'No pending job found'}
        
        if message == 'ACCEPT':
            # Accept the job
            if recent_notifications.gig and recent_notifications.order:
                recent_notifications.gig.job_status = 'in_progress'
                recent_notifications.gig.save()
                
                # Send confirmation
                NotificationService.send_notification(
                    recipient=recent_notifications.recipient,
                    notification_type='job_accepted',
                    title='Job Accepted via SMS',
                    message=f'You have accepted the job: {recent_notifications.gig.title}',
                    channels=['sms', 'in_app']
                )
                
                # Notify client
                NotificationService.send_notification(
                    recipient=recent_notifications.gig.homeowner,
                    notification_type='job_accepted',
                    title='Provider Accepted Job',
                    message=f'{recent_notifications.recipient.first_name} has accepted your job: {recent_notifications.gig.title}',
                    sender=recent_notifications.recipient,
                    gig=recent_notifications.gig,
                    channels=['email', 'sms', 'in_app']
                )
                
                return {'status': 'success', 'message': 'Job accepted successfully'}
        
        return {'status': 'error', 'message': 'Invalid response. Reply ACCEPT to accept the job.'}
