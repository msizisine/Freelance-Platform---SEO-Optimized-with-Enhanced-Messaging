"""
Bank details model for EFT payments - managed by system admin
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BankDetails(models.Model):
    """
    Bank details for EFT payments - only system admin can manage
    """
    ACCOUNT_TYPE_CHOICES = [
        ('cheque', 'Cheque Account'),
        ('savings', 'Savings Account'),
        ('transmission', 'Transmission Account'),
        ('credit_card', 'Credit Card Account'),
    ]
    
    bank_name = models.CharField(max_length=100, help_text="e.g., Standard Bank, FNB, Absa")
    branch_code = models.CharField(max_length=10, help_text="6-digit branch code")
    account_holder_name = models.CharField(max_length=100, help_text="Full name of account holder")
    account_number = models.CharField(max_length=20, help_text="Bank account number")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='cheque')
    is_active = models.BooleanField(default=True, help_text="Whether these bank details are currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bank Details"
        verbose_name_plural = "Bank Details"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_holder_name}"
    
    def get_display_name(self):
        """Get a display name for the bank details"""
        return f"{self.bank_name} ({self.account_holder_name})"


class EFTPaymentConfirmation(models.Model):
    """
    Track EFT payment confirmations from users
    """
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='eft_confirmation')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    proof_of_payment = models.ImageField(upload_to='eft_proofs/', null=True, blank=True, help_text="Upload proof of payment")
    notes = models.TextField(blank=True, help_text="Additional notes about the payment")
    is_verified = models.BooleanField(default=False, help_text="Whether admin has verified the payment")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_eft_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "EFT Payment Confirmation"
        verbose_name_plural = "EFT Payment Confirmations"
        ordering = ['-confirmed_at']
    
    def __str__(self):
        return f"EFT Confirmation for Order {self.order.order_number}"
