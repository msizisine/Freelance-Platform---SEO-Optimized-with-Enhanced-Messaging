from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class Notification(models.Model):
    """Real-time notification model"""
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('job_application', 'Job Application'),
        ('job_offer', 'Job Offer'),
        ('quotation', 'New Quotation'),
        ('payment', 'Payment Received'),
        ('review', 'New Review'),
        ('profile_view', 'Profile Viewed'),
        ('job_completed', 'Job Completed'),
        ('system', 'System Notification'),
        ('saved_search_match', 'Saved Search Match'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Optional related objects
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    data = models.JSONField(default=dict, blank=True)
    
    # Priority
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='normal'
    )
    
    # Action buttons
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_seen(self):
        """Mark notification as seen (for real-time display)"""
        if not self.is_seen:
            self.is_seen = True
            self.save(update_fields=['is_seen'])
    
    def get_related_object(self):
        """Get the related object if available"""
        if self.related_object_type and self.related_object_id:
            try:
                # Map types to models
                model_map = {
                    'message': 'messaging.Message',
                    'job': 'gigs.Gig',
                    'quotation': 'gigs.Quotation',
                    'order': 'orders.Order',
                    'review': 'reviews.Review',
                    'user': 'users.User',
                }
                
                if self.related_object_type in model_map:
                    app_label, model_name = model_map[self.related_object_type].split('.')
                    model_class = apps.get_model(app_label, model_name)
                    return model_class.objects.get(id=self.related_object_id)
            except Exception:
                pass
        return None


class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_messages = models.BooleanField(default=True)
    email_job_applications = models.BooleanField(default=True)
    email_job_offers = models.BooleanField(default=True)
    email_quotations = models.BooleanField(default=True)
    email_payments = models.BooleanField(default=True)
    email_reviews = models.BooleanField(default=True)
    email_saved_searches = models.BooleanField(default=True)
    
    # Push notification preferences
    push_messages = models.BooleanField(default=True)
    push_job_applications = models.BooleanField(default=True)
    push_job_offers = models.BooleanField(default=True)
    push_quotations = models.BooleanField(default=True)
    push_payments = models.BooleanField(default=True)
    push_reviews = models.BooleanField(default=True)
    push_saved_searches = models.BooleanField(default=True)
    
    # In-app preferences
    inapp_messages = models.BooleanField(default=True)
    inapp_job_applications = models.BooleanField(default=True)
    inapp_job_offers = models.BooleanField(default=True)
    inapp_quotations = models.BooleanField(default=True)
    inapp_payments = models.BooleanField(default=True)
    inapp_reviews = models.BooleanField(default=True)
    inapp_saved_searches = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Preferences"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"{self.user.email} Preferences"
    
    def is_quiet_hours(self):
        """Check if current time is during quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # Overnight quiet hours
            return now >= start or now <= end
    
    def should_send_notification(self, notification_type, channel='inapp'):
        """Check if notification should be sent for given type and channel"""
        # Check quiet hours for email and push notifications
        if channel in ['email', 'push'] and self.is_quiet_hours():
            return False
        
        # Check specific preferences
        preference_map = {
            'message': f'{channel}_messages',
            'job_application': f'{channel}_job_applications',
            'job_offer': f'{channel}_job_offers',
            'quotation': f'{channel}_quotations',
            'payment': f'{channel}_payments',
            'review': f'{channel}_reviews',
            'saved_search_match': f'{channel}_saved_searches',
        }
        
        if notification_type in preference_map:
            return getattr(self, preference_map[notification_type], True)
        
        return True


class NotificationChannel(models.Model):
    """WebSocket notification channels"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_channels')
    channel_name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['channel_name']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.channel_name}"
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class NotificationTemplate(models.Model):
    """Templates for different notification types"""
    notification_type = models.CharField(max_length=20)
    title_template = models.CharField(max_length=255)
    message_template = models.TextField()
    
    # Variables available in templates
    variables = models.JSONField(default=list, blank=True, help_text="List of variables available in template")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['notification_type']
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
    
    def __str__(self):
        return f"{self.notification_type} Template"
    
    def render_title(self, context):
        """Render title template with context"""
        from django.template import Template, Context
        template = Template(self.title_template)
        return template.render(Context(context))
    
    def render_message(self, context):
        """Render message template with context"""
        from django.template import Template, Context
        template = Template(self.message_template)
        return template.render(Context(context))


class NotificationBatch(models.Model):
    """Batch notifications for mass sending"""
    name = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Recipients
    recipients = models.ManyToManyField(User, related_name='batch_notifications')
    recipient_filters = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('sending', 'Sending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='draft'
    )
    
    # Scheduling
    send_immediately = models.BooleanField(default=False)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification Batch"
        verbose_name_plural = "Notification Batches"
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def get_recipients(self):
        """Get all recipients based on filters and explicit selections"""
        recipients = set(self.recipients.all())
        
        # Apply filters
        if self.recipient_filters:
            queryset = User.objects.all()
            
            if 'user_type' in self.recipient_filters:
                queryset = queryset.filter(user_type=self.recipient_filters['user_type'])
            
            if 'is_active' in self.recipient_filters:
                queryset = queryset.filter(is_active=self.recipient_filters['is_active'])
            
            if 'location' in self.recipient_filters:
                queryset = queryset.filter(provider_profile__location__icontains=self.recipient_filters['location'])
            
            if 'min_rating' in self.recipient_filters:
                queryset = queryset.filter(provider_profile__average_rating__gte=self.recipient_filters['min_rating'])
            
            recipients.update(queryset)
        
        return list(recipients)
