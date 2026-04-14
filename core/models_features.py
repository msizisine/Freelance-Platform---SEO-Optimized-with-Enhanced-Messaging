from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count
import uuid

User = get_user_model()


class EnhancedReview(models.Model):
    """Enhanced review system with detailed feedback"""
    RATING_CHOICES = [
        (5, 'Excellent'),
        (4, 'Very Good'),
        (3, 'Good'),
        (2, 'Fair'),
        (1, 'Poor'),
    ]
    
    WORK_QUALITY_CHOICES = [
        (5, 'Outstanding'),
        (4, 'Very Good'),
        (3, 'Good'),
        (2, 'Needs Improvement'),
        (1, 'Poor'),
    ]
    
    COMMUNICATION_CHOICES = [
        (5, 'Excellent'),
        (4, 'Very Good'),
        (3, 'Good'),
        (2, 'Fair'),
        (1, 'Poor'),
    ]
    
    TIMELINESS_CHOICES = [
        (5, 'Always on Time'),
        (4, 'Usually on Time'),
        (3, 'Sometimes Late'),
        (2, 'Often Late'),
        (1, 'Very Late'),
    ]
    
    VALUE_CHOICES = [
        (5, 'Excellent Value'),
        (4, 'Good Value'),
        (3, 'Fair Value'),
        (2, 'Overpriced'),
        (1, 'Very Overpriced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic review info
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    gig = models.ForeignKey('gigs.Gig', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    # Overall rating
    overall_rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Detailed ratings
    work_quality = models.IntegerField(choices=WORK_QUALITY_CHOICES, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(choices=COMMUNICATION_CHOICES, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    timeliness = models.IntegerField(choices=TIMELINESS_CHOICES, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    value_for_money = models.IntegerField(choices=VALUE_CHOICES, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Review content
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    
    # Pros and cons
    pros = models.TextField(blank=True, help_text="What went well?")
    cons = models.TextField(blank=True, help_text="What could be improved?")
    
    # Verification and status
    is_verified = models.BooleanField(default=False, help_text="Verified as a genuine review")
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Featured review on provider profile")
    
    # Response from provider
    provider_response = models.TextField(blank=True)
    provider_response_date = models.DateTimeField(null=True, blank=True)
    
    # Helpfulness votes
    helpful_votes = models.PositiveIntegerField(default=0)
    total_votes = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service_provider', 'overall_rating']),
            models.Index(fields=['gig', 'is_public']),
            models.Index(fields=['homeowner', 'created_at']),
            models.Index(fields=['is_verified', 'is_public']),
        ]
        unique_together = [['homeowner', 'service_provider', 'gig']]
    
    def __str__(self):
        return f"Review by {self.homeowner.email} for {self.service_provider.email}"
    
    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings"""
        ratings = []
        if self.work_quality:
            ratings.append(self.work_quality)
        if self.communication:
            ratings.append(self.communication)
        if self.timeliness:
            ratings.append(self.timeliness)
        if self.value_for_money:
            ratings.append(self.value_for_money)
        
        return sum(ratings) / len(ratings) if ratings else self.overall_rating
    
    @property
    def helpfulness_percentage(self):
        """Calculate helpfulness percentage"""
        if self.total_votes == 0:
            return 0
        return (self.helpful_votes / self.total_votes) * 100
    
    def mark_as_helpful(self, helpful=True):
        """Vote on review helpfulness"""
        self.total_votes += 1
        if helpful:
            self.helpful_votes += 1
        self.save(update_fields=['helpful_votes', 'total_votes'])


class PortfolioItem(models.Model):
    """Portfolio items for providers to showcase work"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    
    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey('gigs.Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Media
    image = models.ImageField(upload_to='portfolio/images/', null=True, blank=True)
    video = models.FileField(upload_to='portfolio/videos/', null=True, blank=True)
    
    # Project details
    project_date = models.DateField(null=True, blank=True, help_text="When was this project completed?")
    location = models.CharField(max_length=255, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=100, blank=True, help_text="e.g., 2 weeks, 3 months")
    
    # Status and visibility
    is_featured = models.BooleanField(default=False, help_text="Featured in portfolio")
    is_public = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Tags and skills
    tags = models.JSONField(default=list, blank=True, help_text="List of tags/skills")
    materials_used = models.JSONField(default=list, blank=True, help_text="Materials used in project")
    
    # Client information (optional)
    client_name = models.CharField(max_length=200, blank=True)
    client_testimonial = models.TextField(blank=True)
    
    # Before/after images
    before_image = models.ImageField(upload_to='portfolio/before/', null=True, blank=True)
    after_image = models.ImageField(upload_to='portfolio/after/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['provider', 'is_public']),
            models.Index(fields=['category', 'is_featured']),
            models.Index(fields=['is_public', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.provider.email} - {self.title}"


class AvailabilityCalendar(models.Model):
    """Provider availability and scheduling system"""
    
    provider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='availability_calendar')
    
    # Working hours
    monday_start = models.TimeField(null=True, blank=True)
    monday_end = models.TimeField(null=True, blank=True)
    tuesday_start = models.TimeField(null=True, blank=True)
    tuesday_end = models.TimeField(null=True, blank=True)
    wednesday_start = models.TimeField(null=True, blank=True)
    wednesday_end = models.TimeField(null=True, blank=True)
    thursday_start = models.TimeField(null=True, blank=True)
    thursday_end = models.TimeField(null=True, blank=True)
    friday_start = models.TimeField(null=True, blank=True)
    friday_end = models.TimeField(null=True, blank=True)
    saturday_start = models.TimeField(null=True, blank=True)
    saturday_end = models.TimeField(null=True, blank=True)
    sunday_start = models.TimeField(null=True, blank=True)
    sunday_end = models.TimeField(null=True, blank=True)
    
    # General availability
    advance_booking_days = models.PositiveIntegerField(default=30, help_text="Days in advance clients can book")
    minimum_booking_hours = models.PositiveIntegerField(default=1, help_text="Minimum hours per booking")
    maximum_booking_hours = models.PositiveIntegerField(default=8, help_text="Maximum hours per booking")
    
    # Buffer time between bookings
    buffer_time_minutes = models.PositiveIntegerField(default=30, help_text="Buffer time between bookings")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Availability Calendar"
        verbose_name_plural = "Availability Calendars"
    
    def __str__(self):
        return f"Availability for {self.provider.email}"
    
    def get_working_hours(self, day):
        """Get working hours for a specific day"""
        day_fields = {
            'monday': ('monday_start', 'monday_end'),
            'tuesday': ('tuesday_start', 'tuesday_end'),
            'wednesday': ('wednesday_start', 'wednesday_end'),
            'thursday': ('thursday_start', 'thursday_end'),
            'friday': ('friday_start', 'friday_end'),
            'saturday': ('saturday_start', 'saturday_end'),
            'sunday': ('sunday_start', 'sunday_end'),
        }
        
        start_field, end_field = day_fields.get(day.lower(), (None, None))
        start = getattr(self, start_field, None)
        end = getattr(self, end_field, None)
        
        return (start, end)
    
    def is_available_on_date(self, date):
        """Check if provider is available on a specific date"""
        day_name = date.strftime('%A').lower()
        start, end = self.get_working_hours(day_name)
        return start is not None and end is not None


class AvailabilitySlot(models.Model):
    """Specific availability slots"""
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
        ('unavailable', 'Unavailable'),
    ]
    
    calendar = models.ForeignKey(AvailabilityCalendar, on_delete=models.CASCADE, related_name='slots')
    
    # Date and time
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Booking information
    booking = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='availability_slots')
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['calendar', 'date', 'status']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['booking']),
        ]
        unique_together = [['calendar', 'date', 'start_time']]
    
    def __str__(self):
        return f"{self.calendar.provider.email} - {self.date} {self.start_time} to {self.end_time}"


class Invoice(models.Model):
    """Invoice generation system"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    invoice_number = models.CharField(max_length=50, unique=True)
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices_sent')
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices_received')
    
    # Related order/gig
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    gig = models.ForeignKey('gigs.Gig', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    # Invoice details
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    payment_terms = models.TextField(blank=True)
    
    # PDF generation
    pdf_file = models.FileField(upload_to='invoices/pdf/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['homeowner', 'status']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.provider.email} to {self.homeowner.email}"
    
    def save(self, *args, **kwargs):
        # Calculate VAT and total
        self.vat_amount = self.subtotal * (self.vat_rate / 100)
        self.total_amount = self.subtotal + self.vat_amount
        
        # Generate invoice number if not set
        if not self.invoice_number:
            last_invoice = Invoice.objects.filter(
                created_at__year=timezone.now().year
            ).order_by('-created_at').first()
            
            if last_invoice:
                try:
                    last_number = int(last_invoice.invoice_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.invoice_number = f"INV-{timezone.now().year}-{new_number:04d}"
        
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Line items for invoices"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    # Item details
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Optional reference to gig/service
    gig = models.ForeignKey('gigs.Gig', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_items')
    
    # Sort order
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Dispute(models.Model):
    """Dispute resolution system"""
    
    STATUS_CHOICES = [
        ('opened', 'Opened'),
        ('investigating', 'Investigating'),
        ('mediating', 'Mediating'),
        ('resolved', 'Resolved'),
        ('escalated', 'Escalated'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Parties involved
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disputes_initiated')
    respondent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disputes_received')
    
    # Related order/gig
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes')
    gig = models.ForeignKey('gigs.Gig', on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes')
    
    # Dispute details
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, help_text="Type of dispute")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='opened')
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolution_date = models.DateTimeField(null=True, blank=True)
    mediator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mediated_disputes')
    
    # Compensation (if any)
    compensation_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    compensation_paid = models.BooleanField(default=False)
    compensation_date = models.DateTimeField(null=True, blank=True)
    
    # Evidence
    evidence_files = models.JSONField(default=list, blank=True)
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['initiator', 'status']),
            models.Index(fields=['respondent', 'status']),
            models.Index(fields=['order', 'status']),
        ]
    
    def __str__(self):
        return f"Dispute: {self.title} ({self.initiator.email} vs {self.respondent.email})"


class DisputeMessage(models.Model):
    """Messages within a dispute"""
    
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dispute_messages')
    
    message = models.TextField()
    is_public = models.BooleanField(default=True, help_text="Visible to both parties")
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message in {self.dispute.title} by {self.sender.email}"


class UserAnalytics(models.Model):
    """User statistics and insights"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Profile views
    profile_views = models.PositiveIntegerField(default=0)
    profile_views_last_30_days = models.PositiveIntegerField(default=0)
    
    # Gigs/Orders stats
    total_gigs_created = models.PositiveIntegerField(default=0)
    active_gigs = models.PositiveIntegerField(default=0)
    total_orders_received = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    
    # Financial stats
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    earnings_last_30_days = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Response stats
    average_response_time_minutes = models.PositiveIntegerField(default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Review stats
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_last_30_days = models.PositiveIntegerField(default=0)
    
    # Search visibility
    search_appearances = models.PositiveIntegerField(default=0)
    search_clicks = models.PositiveIntegerField(default=0)
    search_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Last updated
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Analytics"
        verbose_name_plural = "User Analytics"
    
    def __str__(self):
        return f"Analytics for {self.user.email}"
    
    def update_stats(self):
        """Update all statistics"""
        self._update_gig_stats()
        self._update_order_stats()
        self._update_financial_stats()
        self._update_review_stats()
        self._update_response_stats()
        self._update_search_stats()
        self.save()
    
    def _update_gig_stats(self):
        """Update gig-related statistics"""
        from gigs.models import Gig
        
        self.total_gigs_created = Gig.objects.filter(user=self.user).count()
        self.active_gigs = Gig.objects.filter(user=self.user, is_active=True).count()
    
    def _update_order_stats(self):
        """Update order-related statistics"""
        from orders.models import Order
        
        orders = Order.objects.filter(gig__user=self.user)
        self.total_orders_received = orders.count()
        self.completed_orders = orders.filter(status='completed').count()
        self.cancelled_orders = orders.filter(status='cancelled').count()
    
    def _update_financial_stats(self):
        """Update financial statistics"""
        from orders.models import Order
        
        completed_orders = Order.objects.filter(
            gig__user=self.user, 
            status='completed'
        )
        
        if completed_orders.exists():
            total = completed_orders.aggregate(
                total=models.Sum('total_amount')
            )['total'] or 0
            self.total_earnings = total
            self.average_order_value = total / completed_orders.count()
    
    def _update_review_stats(self):
        """Update review statistics"""
        reviews = EnhancedReview.objects.filter(service_provider=self.user)
        self.total_reviews = reviews.count()
        
        if reviews.exists():
            avg_rating = reviews.aggregate(
                avg=models.Avg('overall_rating')
            )['avg'] or 0
            self.average_rating = avg_rating
    
    def _update_response_stats(self):
        """Update response time statistics"""
        # This would be implemented based on message response times
        pass
    
    def _update_search_stats(self):
        """Update search visibility statistics"""
        # This would be implemented based on search analytics
        pass
