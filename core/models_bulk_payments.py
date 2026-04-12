"""
Bulk Payment Models for tracking payment batches
"""
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class PaymentBatch(models.Model):
    """Model to track bulk payment batches"""
    
    BATCH_TYPES = [
        ('ewallet', 'eWallet Bulk Payment'),
        ('eft', 'EFT Bulk Payment'),
        ('mixed', 'Mixed Payment Types'),
    ]
    
    STATUS_CHOICES = [
        ('generated', 'CSV Generated'),
        ('uploaded', 'Uploaded to Bank'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_type = models.CharField(max_length=20, choices=BATCH_TYPES, default='mixed')
    payout_count = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    csv_content = models.TextField(help_text="CSV content for bank upload")
    csv_filename = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    bank_reference = models.CharField(max_length=100, blank=True, help_text="Bank transaction reference")
    error_message = models.TextField(blank=True, help_text="Error details if batch failed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    payouts = models.ManyToManyField('core.ProviderPayout', related_name='payment_batches')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_batches')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Payment Batches"
    
    def __str__(self):
        return f"PaymentBatch {self.id} - {self.get_batch_type_display()} ({self.payout_count} payouts)"
    
    @property
    def filename(self):
        """Generate filename for CSV download"""
        timestamp = self.created_at.strftime('%Y%m%d_%H%M%S')
        return f"{self.batch_type}_batch_{timestamp}_{self.id}.csv"
    
    def mark_as_uploaded(self, bank_reference=''):
        """Mark batch as uploaded to bank"""
        from django.utils import timezone
        self.status = 'uploaded'
        self.uploaded_at = timezone.now()
        if bank_reference:
            self.bank_reference = bank_reference
        self.save()
    
    def mark_as_completed(self):
        """Mark batch as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update associated payouts to completed status
        self.payouts.update(status='completed')
    
    def mark_as_failed(self, error_message=''):
        """Mark batch as failed"""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()


class BulkPaymentSettings(models.Model):
    """Settings for bulk payment processing"""
    
    # FNB Settings
    fnb_business_account = models.CharField(max_length=50, help_text="FNB Business Account Number")
    fnb_branch_code = models.CharField(max_length=10, help_text="FNB Branch Code")
    
    # Processing Settings
    auto_process_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Minimum number of payouts to trigger auto-processing"
    )
    processing_fee_ewallet = models.DecimalField(
        max_digits=6, decimal_places=2, default=1.50,
        help_text="Fee per eWallet transaction"
    )
    processing_fee_eft = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.00,
        help_text="Fee per EFT transaction"
    )
    
    # Notification Settings
    notify_on_completion = models.BooleanField(default=True)
    notification_email = models.EmailField(blank=True)
    
    # Security Settings
    require_dual_approval = models.BooleanField(default=False)
    approval_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_batches', help_text="User required for approval"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bulk Payment Settings"
        verbose_name_plural = "Bulk Payment Settings"
    
    def __str__(self):
        return f"Bulk Payment Settings (FNB: {self.fnb_business_account})"
