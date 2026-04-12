"""
Django signals to trigger WhatsApp notifications for messages
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Message
from notifications.enhanced_services import EnhancedNotificationService

User = get_user_model()

@receiver(post_save, sender=Message)
def send_whatsapp_notification(sender, instance, created, **kwargs):
    """
    Send WhatsApp notification when a new message is created
    """
    if not created:
        return  # Only notify for new messages
    
    # Get the recipient (other participant in conversation)
    recipient = instance.conversation.get_other_participant(instance.sender)
    
    if not recipient:
        return
    
    # Only send if recipient has phone number
    if not recipient.phone:
        return
    
    # Create personalized message with recipient name
    recipient_name = recipient.first_name or recipient.email.split('@')[0]
    sender_name = instance.sender.first_name or instance.sender.email.split('@')[0]
    
    # Prepare message content
    message_content = f"New message from {sender_name}: {instance.content[:100]}{'...' if len(instance.content) > 100 else ''}"
    
    try:
        # Send WhatsApp notification with fallback
        result = EnhancedNotificationService.send_with_fallback(
            recipient=recipient,
            notification_type='new_message',
            title=f'New Message from {sender_name}',
            message=message_content,
            channels=['whatsapp', 'sms', 'email'],
            context={
                'recipient_name': recipient_name,
                'sender_name': sender_name,
                'message_content': instance.content,
                'conversation_url': f"/messages/{instance.conversation.pk}/",
                'content_sid': 'HXb5b62575e6e4ff6129ad7c8efe1f983e',
                'content_variables': f'{{"1":"{recipient_name}","2":"{sender_name}"}}'
            }
        )
        
        print(f"WhatsApp notification sent for message {instance.pk}: {result['overall_success']}")
        
    except Exception as e:
        print(f"Error sending WhatsApp notification: {e}")
