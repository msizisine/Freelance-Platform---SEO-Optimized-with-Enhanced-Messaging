from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Notification(models.Model):
    """Central notification model for all app communications"""
    
    NOTIFICATION_TYPES = [
        ('job_applied', 'Job Applied'),
        ('job_accepted', 'Job Accepted'),
        ('job_rejected', 'Job Rejected'),
        ('job_completed', 'Job Completed'),
        ('order_created', 'Order Created'),
        ('payment_received', 'Payment Received'),
        ('review_received', 'Review Received'),
        ('message_received', 'Message Received'),
        ('provider_verified', 'Provider Verified'),
        ('provider_unverified', 'Provider Unverified'),
        ('quotation_received', 'Quotation Received'),
        ('quotation_accepted', 'Quotation Accepted'),
        ('quotation_rejected', 'Quotation Rejected'),
        ('account_created', 'Account Created'),
        ('password_reset', 'Password Reset'),
        ('otp_login', 'OTP Login'),
    ]
    
    CHANNELS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('in_app', 'In-App'),
        ('push', 'Push Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    channels = models.CharField(max_length=20, choices=CHANNELS, default='in_app')
    
    # Related objects for context
    gig = models.ForeignKey('gigs.Gig', on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    review = models.ForeignKey('reviews.Review', on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey('messaging.Conversation', on_delete=models.CASCADE, null=True, blank=True)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    send_attempts = models.PositiveIntegerField(default=0)
    last_attempt = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['channels']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class NotificationTemplate(models.Model):
    """Templates for different notification types"""
    
    notification_type = models.CharField(max_length=50, unique=True)
    subject_template = models.CharField(max_length=200, help_text="Email subject template")
    email_template = models.TextField(help_text="Email body template")
    sms_template = models.CharField(max_length=500, help_text="SMS template (max 500 chars)")
    whatsapp_template = models.CharField(max_length=1000, help_text="WhatsApp template")
    in_app_template = models.TextField(help_text="In-app notification template")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['notification_type']
    
    def __str__(self):
        return f"{self.notification_type} Template"


class OTPCode(models.Model):
    """OTP codes for SMS/WhatsApp authentication"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)
    phone_number = models.CharField(max_length=20)
    channel = models.CharField(max_length=10, choices=[('sms', 'SMS'), ('whatsapp', 'WhatsApp')])
    purpose = models.CharField(max_length=20, choices=[
        ('login', 'Login'),
        ('verify', 'Phone Verification'),
        ('password_reset', 'Password Reset'),
    ])
    
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used']),
            models.Index(fields=['code', 'expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.purpose}"
    
    def is_valid(self):
        """Check if OTP is valid and not expired"""
        return not self.is_used and timezone.now() < self.expires_at and self.attempts < 3
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])


class CommunicationLog(models.Model):
    """Log of all communication attempts"""
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='communication_logs')
    channel = models.CharField(max_length=20, choices=Notification.CHANNELS)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ])
    provider_response = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # External IDs for tracking
    external_id = models.CharField(max_length=100, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['channel', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.channel} - {self.status} for {self.notification.title}"


class NotificationPreference(models.Model):
    """User preferences for notification channels"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=50, choices=Notification.NOTIFICATION_TYPES)
    
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'notification_type']
        ordering = ['user', 'notification_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.notification_type}"


class SMSMessage(models.Model):
    """SMS messages for sending via various providers"""
    
    recipient = models.CharField(max_length=20)
    message = models.TextField()
    sender_id = models.CharField(max_length=50, default='FreelancePlatform')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Provider details
    provider = models.CharField(max_length=50, choices=[
        ('twilio', 'Twilio'),
        ('africastalking', 'Africa\'s Talking'),
        ('messagebird', 'MessageBird'),
    ], default='twilio')
    
    # Response data
    provider_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Related notification
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, null=True, blank=True, related_name='sms_messages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS to {self.recipient} - {self.status}"


class WhatsAppMessage(models.Model):
    """WhatsApp messages for sending via various providers"""
    
    recipient = models.CharField(max_length=20)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('template', 'Template'),
        ('media', 'Media'),
    ], default='text')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], default='pending')
    
    # Provider details
    provider = models.CharField(max_length=50, choices=[
        ('twilio', 'Twilio'),
        ('meta', 'Meta Business API'),
        ('messagebird', 'MessageBird'),
    ], default='twilio')
    
    # Response data
    provider_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    external_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Related notification
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, null=True, blank=True, related_name='whatsapp_messages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"WhatsApp to {self.recipient} - {self.status}"
