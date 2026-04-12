from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from gigs.models import Gig
import uuid

User = get_user_model()

# Import bank details models
from .models_bank import BankDetails, EFTPaymentConfirmation


class JobOffer(models.Model):
    """Model for tracking job offers and estimates from service providers"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Estimate Submitted'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_offers_received')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_offers_sent')
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, null=True, blank=True)
    
    # Job details from homeowner
    job_title = models.CharField(max_length=200)
    job_description = models.TextField()
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Service provider's estimate
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_duration = models.CharField(max_length=100, null=True, blank=True, help_text="Estimated time to complete")
    estimate_description = models.TextField(null=True, blank=True, help_text="Description of the estimate and approach")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Order relationship
    order = models.OneToOneField('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='job_offer')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job Offer: {self.job_title} - {self.homeowner.email} to {self.service_provider.email}"
    
    def approve(self):
        """Approve the estimate and create a job"""
        from django.utils import timezone
        
        # Create the gig if it doesn't exist
        if not self.gig:
            self.gig = Gig.objects.create(
                title=self.job_title,
                description=self.job_description,
                homeowner=self.homeowner,
                is_private=True,
                hired_provider=self.service_provider,
                job_status='accepted',
                budget_min=self.budget_min,
                budget_max=self.budget_max,
                is_active=True
            )
        
        # Create order
        import uuid
        
        # Ensure we have a valid gig
        if not self.gig:
            self.gig = Gig.objects.create(
                title=self.job_title,
                description=self.job_description,
                homeowner=self.homeowner,
                is_private=True,
                hired_provider=self.service_provider,
                job_status='accepted',
                budget_min=self.budget_min,
                budget_max=self.budget_max,
                is_active=True
            )
        
        order = Order.objects.create(
            id=uuid.uuid4(),  # Explicitly generate UUID
            homeowner=self.homeowner,
            service_provider=self.service_provider,
            gig=self.gig,  # Now guaranteed to be non-None
            requirements=self.job_description,
            total_amount=self.estimated_price,
            status='accepted',
            due_date=timezone.now() + timezone.timedelta(days=7)  # Default 7 days
        )
        
        # Update status and save order reference
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.order = order
        self.save()
        
        return order


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('revision_requested', 'Revision Requested'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('yoco', 'Yoco (Card Payment)'),
        ('ozow', 'Ozow (Instant EFT)'),
        ('eft', 'EFT Transfer'),
        ('in_person', 'In-Person Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True)
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homeowner_orders', null=True)
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_provider_orders', null=True, blank=True)
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    
    # Order details
    requirements = models.TextField(help_text="Homeowner's specific requirements for this order")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='in_app', help_text="How the homeowner will pay the service provider")
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField()
    
    # Payment tracking
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    ozow_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Files
    delivery_files = models.ManyToManyField('OrderFile', blank=True)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.gig.title}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    def mark_as_paid(self):
        """Mark order as paid and create payment receipt"""
        from core.models_receipts import PaymentReceipt
        import random
        import string
        
        self.payment_status = 'paid'
        self.save()
        
        # Create payment receipt if it doesn't exist
        if not PaymentReceipt.objects.filter(order=self).exists():
            # Map payment methods
            payment_method_map = {
                'ozow': 'ozow',
                'eft': 'eft', 
                'in_person': 'cash',
                'yoco': 'card'
            }
            
            receipt_method = payment_method_map.get(self.payment_method, 'other')
            
            # Generate receipt number
            receipt_number = 'REC-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            PaymentReceipt.objects.create(
                homeowner=self.homeowner,
                order=self,
                payment_method=receipt_method,
                payment_status='completed',
                amount=self.total_amount,
                receipt_number=receipt_number,
                payment_date=timezone.now(),
                description=f"Payment for Order {self.order_number} - {self.gig.title}",
                confirmed_at=timezone.now()
            )
    
    def accept_order(self):
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
    
    def reject_order(self):
        self.status = 'rejected'
        self.save()
    
    def start_progress(self):
        self.status = 'in_progress'
        self.save()
    
    def deliver_order(self):
        self.status = 'delivered'
        self.save()
    
    def request_revision(self):
        self.status = 'revision_requested'
        self.save()
    
    def complete_order(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def cancel_order(self):
        self.status = 'cancelled'
        self.save()
    
    def is_overdue(self):
        from django.utils import timezone
        return timezone.now() > self.due_date and self.status not in ['completed', 'cancelled']


class OrderFile(models.Model):
    file = models.FileField(upload_to='order_files/')
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.filename} - {self.uploaded_by.email}"


class OrderMessage(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    file_attachment = models.FileField(upload_to='order_messages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message for {self.order.order_number} by {self.sender.email}"


class OrderRevision(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='revisions')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revision_requests')
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Revision for {self.order.order_number}"


class OrderDispute(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='dispute')
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('under_review', 'Under Review'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed')
        ],
        default='open'
    )
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Dispute for {self.order.order_number}"


class OrderTracking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Tracking for {self.order.order_number} - {self.status}"
