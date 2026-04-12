"""
Quote Request Models for WhatsApp Flow Integration
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class QuoteRequest(models.Model):
    """Quote request from homeowner to service provider"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Request details
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quote_requests')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_quotes')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    service_category = models.CharField(max_length=100)
    
    # Location and timing
    location = models.CharField(max_length=255)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    is_flexible = models.BooleanField(default=False)
    
    # Budget and priority
    budget_range = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # WhatsApp integration
    whatsapp_flow_id = models.CharField(max_length=100, blank=True)
    whatsapp_message_id = models.CharField(max_length=100, blank=True)
    whatsapp_response_data = models.JSONField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['homeowner', 'status']),
            models.Index(fields=['service_provider', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Quote Request: {self.title} - {self.homeowner.email}"
    
    def is_expired(self):
        """Check if quote request has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def mark_as_responded(self):
        """Mark quote request as responded"""
        self.status = 'responded'
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])


class QuoteResponse(models.Model):
    """Service provider's response to quote request"""
    
    RESPONSE_TYPES = [
        ('quote', 'Formal Quote'),
        ('question', 'Question'),
        ('declined', 'Declined'),
        ('accepted', 'Accepted'),
    ]
    
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='responses')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE)
    
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    
    # Quote details
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_description = models.TextField(blank=True)
    
    # Timeline
    estimated_days = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    
    # Message content
    message = models.TextField()
    attachments = models.JSONField(null=True, blank=True)  # Store file URLs
    
    # WhatsApp integration
    whatsapp_flow_response = models.JSONField(null=True, blank=True)
    whatsapp_message_id = models.CharField(max_length=100, blank=True)
    
    # Status
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Response to {self.quote_request.title} by {self.service_provider.email}"


class WhatsAppFlowTemplate(models.Model):
    """WhatsApp Flow templates for different interactions"""
    
    FLOW_TYPES = [
        ('quote_request', 'Quote Request'),
        ('quote_response', 'Quote Response'),
        ('service_confirmation', 'Service Confirmation'),
        ('feedback', 'Feedback Collection'),
    ]
    
    name = models.CharField(max_length=100)
    flow_type = models.CharField(max_length=30, choices=FLOW_TYPES)
    flow_json = models.JSONField()  # WhatsApp Flow definition
    
    # WhatsApp Business API IDs
    flow_id = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20, default='1.0')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['flow_type', 'name']
    
    def __str__(self):
        return f"{self.flow_type}: {self.name}"


class WhatsAppInteraction(models.Model):
    """Track all WhatsApp interactions for analytics and debugging"""
    
    INTERACTION_TYPES = [
        ('flow_started', 'Flow Started'),
        ('flow_completed', 'Flow Completed'),
        ('flow_abandoned', 'Flow Abandoned'),
        ('message_sent', 'Message Sent'),
        ('message_received', 'Message Received'),
        ('button_clicked', 'Button Clicked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    
    # Related objects
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, null=True, blank=True)
    quote_response = models.ForeignKey(QuoteResponse, on_delete=models.CASCADE, null=True, blank=True)
    flow_template = models.ForeignKey(WhatsAppFlowTemplate, on_delete=models.CASCADE, null=True, blank=True)
    
    # WhatsApp data
    whatsapp_message_id = models.CharField(max_length=100, blank=True)
    whatsapp_flow_id = models.CharField(max_length=100, blank=True)
    payload = models.JSONField(null=True, blank=True)
    
    # Response tracking
    response_data = models.JSONField(null=True, blank=True)
    processing_status = models.CharField(max_length=20, default='pending')
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'interaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.interaction_type} - {self.phone_number}"
