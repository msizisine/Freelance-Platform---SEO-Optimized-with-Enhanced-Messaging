"""
Payment processing models for provider payouts and fee management
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class ProviderEarnings(models.Model):
    """
    Track earnings for service providers before deductions
    """
    EARNING_TYPES = [
        ('job_completion', 'Job Completion'),
        ('milestone', 'Milestone Payment'),
        ('bonus', 'Bonus Payment'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('available', 'Available for Withdrawal'),
        ('processing', 'Processing Payment'),
        ('paid', 'Paid'),
        ('frozen', 'Frozen - Under Review'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey('core.User', on_delete=models.CASCADE, limit_choices_to={'user_type': 'service_provider'})
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    earning_type = models.CharField(max_length=20, choices=EARNING_TYPES, default='job_completion')
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount before deductions")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Platform commission deducted")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount after commission deduction")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, help_text="Description of the earning")
    created_at = models.DateTimeField(auto_now_add=True)
    available_at = models.DateTimeField(null=True, blank=True, help_text="When earning becomes available for withdrawal")
    
    class Meta:
        verbose_name = "Provider Earning"
        verbose_name_plural = "Provider Earnings"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.email} - {self.get_earning_type_display()} - R{self.net_amount}"
    
    def calculate_commission(self):
        """Calculate commission based on platform settings"""
        from .models_config import SystemConfiguration
        try:
            commission_rate = SystemConfiguration.objects.get(key='commission_rate').get_value()
            commission_rate = Decimal(str(commission_rate))
            return self.gross_amount * (commission_rate / Decimal('100'))
        except SystemConfiguration.DoesNotExist:
            return self.gross_amount * Decimal('0.10')  # Default 10%
    
    def save(self, *args, **kwargs):
        # Calculate commission and net amount if not set
        if not self.commission_amount:
            self.commission_amount = self.calculate_commission()
        if not self.net_amount:
            self.net_amount = self.gross_amount - self.commission_amount
        
        # Set availability date (2 days after earning becomes available)
        if self.status == 'available' and not self.available_at:
            from django.utils import timezone
            from datetime import timedelta
            self.available_at = timezone.now() + timedelta(days=2)
        
        super().save(*args, **kwargs)


class ProviderPayout(models.Model):
    """
    Track payouts to service providers
    """
    PAYOUT_METHODS = [
        ('ewallet', 'E-Wallet'),
        ('cash_send', 'Cash Send'),
        ('payshap', 'PayShap'),
        ('bank_transfer', 'Bank Transfer'),
        ('instant_payment', 'Instant Payment'),
        ('manual', 'Manual Payment'),
    ]
    
    STATUS_CHOICES = [
        ('requested', 'Payment Requested'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('standard', 'Standard (2 days)'),
        ('urgent', 'Urgent (Immediate)'),
        ('express', 'Express (Same day)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey('core.User', on_delete=models.CASCADE, limit_choices_to={'user_type': 'service_provider'})
    earnings = models.ManyToManyField(ProviderEarnings, help_text="Earnings included in this payout")
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total gross amount before fees")
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Platform service fee")
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Processing fee for urgent payments")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Final amount to be paid")
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='standard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    
    # Payment details
    recipient_name = models.CharField(max_length=100, help_text="Full name of recipient")
    recipient_phone = models.CharField(max_length=20, blank=True, help_text="Phone number for mobile payments")
    recipient_email = models.CharField(max_length=100, blank=True, help_text="Email for e-wallet payments")
    bank_account = models.CharField(max_length=100, blank=True, help_text="Bank account number")
    bank_name = models.CharField(max_length=100, blank=True, help_text="Bank name")
    branch_code = models.CharField(max_length=20, blank=True, help_text="Bank branch code")
    
    # Reference and tracking
    reference_number = models.CharField(max_length=50, unique=True, help_text="Unique reference for this payout")
    transaction_id = models.CharField(max_length=100, blank=True, help_text="External transaction ID")
    receipt_url = models.URLField(blank=True, help_text="URL to payment receipt")
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes and admin
    notes = models.TextField(blank=True, help_text="Provider notes for this payout")
    admin_notes = models.TextField(blank=True, help_text="Admin internal notes")
    
    class Meta:
        verbose_name = "Provider Payout"
        verbose_name_plural = "Provider Payouts"
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Payout to {self.provider.email} - R{self.net_amount}"
    
    def calculate_fees(self):
        """Calculate platform and processing fees based on priority"""
        from .models_config import SystemConfiguration, PlatformFee
        
        # Platform service fee
        try:
            service_fee_config = PlatformFee.objects.get(fee_type='service_fee', is_active=True)
            platform_fee = service_fee_config.fee_fixed
            if service_fee_config.fee_percentage > 0:
                platform_fee += self.gross_amount * (service_fee_config.fee_percentage / Decimal('100'))
        except PlatformFee.DoesNotExist:
            platform_fee = Decimal('5.00')  # Default service fee
        
        # Processing fee for urgent payments
        processing_fee = Decimal('0.00')
        if self.priority == 'urgent':
            processing_fee = Decimal('15.00')  # R15 extra for immediate
        elif self.priority == 'express':
            processing_fee = Decimal('25.00')  # R25 extra for same day
        
        return platform_fee, processing_fee
    
    def save(self, *args, **kwargs):
        # Calculate fees and net amount if not set
        if not self.platform_fee or not self.processing_fee:
            platform_fee, processing_fee = self.calculate_fees()
            self.platform_fee = platform_fee
            self.processing_fee = processing_fee
        
        if not self.net_amount:
            self.net_amount = self.gross_amount - self.platform_fee - self.processing_fee
        
        # Generate reference number if not set
        if not self.reference_number:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.reference_number = f"PAY{self.provider.id}{timestamp}"
        
        super().save(*args, **kwargs)


class MonthlyServiceFee(models.Model):
    """
    Track monthly service fees charged to providers
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('charged', 'Charged'),
        ('paid', 'Paid'),
        ('waived', 'Waived'),
        ('overdue', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey('core.User', on_delete=models.CASCADE, limit_choices_to={'user_type': 'service_provider'})
    month = models.DateField(help_text="Month for which fee is charged")
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Base monthly service fee")
    additional_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Additional fees for the month")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5.00, help_text="Total fee for the month")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment tracking
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Amount paid towards this fee")
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Notes about this monthly fee")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Monthly Service Fee"
        verbose_name_plural = "Monthly Service Fees"
        unique_together = ['provider', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.provider.email} - {self.month.strftime('%B %Y')} - R{self.total_fee}"
    
    def calculate_monthly_fee(self):
        """Calculate monthly fee based on platform settings"""
        from .models_config import SystemConfiguration
        
        # Get base service fee
        try:
            service_fee_config = SystemConfiguration.objects.get(key='platform_service_fee')
            base_fee = Decimal(str(service_fee_config.get_value()))
        except SystemConfiguration.DoesNotExist:
            base_fee = Decimal('5.00')  # Default R5 per month
        
        # Calculate additional fees based on provider activity
        additional_fees = Decimal('0.00')
        
        # Add fee for high volume providers (more than 10 jobs per month)
        from django.utils import timezone
        from datetime import timedelta
        month_start = self.month.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        job_count = ProviderEarnings.objects.filter(
            provider=self.provider,
            created_at__range=[month_start, month_end],
            earning_type='job_completion'
        ).count()
        
        if job_count > 10:
            additional_fees = additional_fees + Decimal('10.00')  # Extra R10 for high volume
        
        self.base_fee = base_fee
        self.additional_fees = additional_fees
        self.total_fee = base_fee + additional_fees
        
        return self.total_fee


class PaymentTransaction(models.Model):
    """
    Track all payment transactions for auditing
    """
    TRANSACTION_TYPES = [
        ('earning', 'Earning Credit'),
        ('payout', 'Payout Debit'),
        ('fee', 'Fee Charge'),
        ('refund', 'Refund'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey('core.User', on_delete=models.CASCADE, limit_choices_to={'user_type': 'service_provider'})
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    earning = models.ForeignKey(ProviderEarnings, on_delete=models.CASCADE, null=True, blank=True)
    payout = models.ForeignKey(ProviderPayout, on_delete=models.CASCADE, null=True, blank=True)
    monthly_fee = models.ForeignKey(MonthlyServiceFee, on_delete=models.CASCADE, null=True, blank=True)
    
    # Details
    description = models.TextField(help_text="Transaction description")
    reference_number = models.CharField(max_length=50, blank=True, help_text="Reference number for this transaction")
    external_transaction_id = models.CharField(max_length=100, blank=True, help_text="External system transaction ID")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.provider.email} - {self.get_transaction_type_display()} - R{self.amount}"
