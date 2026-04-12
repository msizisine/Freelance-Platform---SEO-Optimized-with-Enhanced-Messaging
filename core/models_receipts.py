"""
Models for tracking payment receipts and transactions
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class PaymentReceipt(models.Model):
    """
    Track all payment receipts from homeowners for orders
    """
    PAYMENT_METHODS = [
        ('eft', 'EFT Transfer'),
        ('ozow', 'Ozow Payment'),
        ('cash', 'Cash Payment'),
        ('card', 'Card Payment'),
        ('other', 'Other Method'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_receipts')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payment_receipts', null=True, blank=True)
    
    # Payment Details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='eft')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Reference Information
    transaction_reference = models.CharField(max_length=100, blank=True, help_text="Bank reference or transaction ID")
    receipt_number = models.CharField(max_length=50, unique=True, help_text="Unique receipt number")
    
    # Payment Method Specific Details
    bank_name = models.CharField(max_length=100, blank=True, help_text="Bank name for EFT payments")
    account_holder = models.CharField(max_length=100, blank=True, help_text="Account holder name")
    payment_date = models.DateTimeField(help_text="Date payment was made or confirmed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When payment was confirmed")
    
    # Notes and Description
    description = models.TextField(blank=True, help_text="Payment description or notes")
    admin_notes = models.TextField(blank=True, help_text="Internal admin notes")
    
    class Meta:
        verbose_name = "Payment Receipt"
        verbose_name_plural = "Payment Receipts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['homeowner', '-created_at']),
            models.Index(fields=['payment_method', '-created_at']),
            models.Index(fields=['payment_status', '-created_at']),
            models.Index(fields=['receipt_number']),
        ]
    
    def __str__(self):
        return f"{self.homeowner.email} - {self.get_payment_method_display()} - R{self.amount}"
    
    @property
    def is_completed(self):
        """Check if payment is completed"""
        return self.payment_status == 'completed'
    
    @property
    def days_since_payment(self):
        """Calculate days since payment date"""
        if self.payment_date:
            return (timezone.now().date() - self.payment_date.date()).days
        return 0
    
    def get_provider_payout_status(self):
        """Check if the service provider has been paid out for this receipt"""
        # For in-person payments, the provider is always considered paid out
        # since they receive payment directly from the homeowner
        if self.payment_method == 'cash':
            return {
                'status': 'paid',
                'display': 'Direct Payment',
                'badge_class': 'bg-success',
                'description': 'Provider paid directly by homeowner'
            }
        
        # For other payment methods, check if there's a corresponding payout
        if self.order and self.order.service_provider:
            from .models_payments import ProviderPayout, ProviderEarnings
            
            # Check if there are completed payouts for this order/provider
            completed_payouts = ProviderPayout.objects.filter(
                provider=self.order.service_provider,
                status='completed'
            ).filter(
                earnings__order=self.order
            )
            
            if completed_payouts.exists():
                return {
                    'status': 'paid',
                    'display': 'Paid Out',
                    'badge_class': 'bg-success',
                    'description': f'Payout completed: {completed_payouts.first().created_at.strftime("%Y-%m-%d")}'
                }
            
            # Check if there are pending payouts
            pending_payouts = ProviderPayout.objects.filter(
                provider=self.order.service_provider,
                status__in=['requested', 'processing', 'approved']
            ).filter(
                earnings__order=self.order
            )
            
            if pending_payouts.exists():
                return {
                    'status': 'pending',
                    'display': 'Payout Pending',
                    'badge_class': 'bg-warning',
                    'description': f'Payout {pending_payouts.first().get_status_display()}'
                }
            
            # Check if earnings are available but not yet requested
            available_earnings = ProviderEarnings.objects.filter(
                provider=self.order.service_provider,
                order=self.order,
                status='available'
            )
            
            if available_earnings.exists():
                return {
                    'status': 'available',
                    'display': 'Available',
                    'badge_class': 'bg-info',
                    'description': 'Earnings available for withdrawal'
                }
        
        # Default status
        return {
            'status': 'unpaid',
            'display': 'Not Paid',
            'badge_class': 'bg-secondary',
            'description': 'No payout record found'
        }


class ReceiptTransaction(models.Model):
    """
    Track all financial transactions in the system
    """
    TRANSACTION_TYPES = [
        ('homeowner_payment', 'Homeowner Payment'),
        ('provider_payout', 'Provider Payout'),
        ('platform_fee', 'Platform Fee'),
        ('commission', 'Commission'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
    ]
    
    # Related Objects
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provider_transactions', null=True, blank=True)
    payment_receipt = models.ForeignKey(PaymentReceipt, on_delete=models.CASCADE, related_name='receipt_transactions', null=True, blank=True)
    
    # Transaction Details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Status and Processing
    status = models.CharField(max_length=20, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - R{self.amount}"
