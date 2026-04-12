"""
Provider bank account models for managing payout accounts
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone

User = get_user_model()


class ProviderBankAccount(models.Model):
    """
    Bank account details for service providers to receive payouts
    """
    ACCOUNT_TYPES = [
        ('cheque', 'Cheque Account'),
        ('savings', 'Savings Account'),
        ('transmission', 'Transmission Account'),
        ('credit_card', 'Credit Card Account'),
        ('business', 'Business Account'),
    ]
    
    BANKS = [
        ('standard_bank', 'Standard Bank'),
        ('fnb', 'First National Bank (FNB)'),
        ('absa', 'Absa Bank'),
        ('nedbank', 'Nedbank'),
        ('capitec', 'Capitec Bank'),
        ('investec', 'Investec'),
        ('african_bank', 'African Bank'),
        ('tymebank', 'TymeBank'),
        ('bidvest_bank', 'Bidvest Bank'),
        ('discovery_bank', 'Discovery Bank'),
        ('other', 'Other'),
    ]
    
    # Account Information
    provider = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'service_provider'}, related_name='bank_accounts')
    account_name = models.CharField(max_length=100, help_text="Account name/label for your reference")
    
    # Bank Details
    bank = models.CharField(max_length=20, choices=BANKS, help_text="Select your bank")
    other_bank_name = models.CharField(max_length=100, blank=True, help_text="Specify if 'Other' bank selected")
    account_holder_name = models.CharField(max_length=100, help_text="Full name as it appears on the bank account")
    account_number = models.CharField(
        max_length=20, 
        validators=[RegexValidator(r'^[0-9]+$', 'Account number must contain only digits')],
        help_text="Bank account number (digits only)"
    )
    branch_code = models.CharField(
        max_length=6,
        validators=[RegexValidator(r'^[0-9]{6}$', 'Branch code must be exactly 6 digits')],
        help_text="6-digit branch code"
    )
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='cheque')
    
    # Verification and Status
    is_verified = models.BooleanField(default=False, help_text="Whether this account has been verified by admin")
    is_active = models.BooleanField(default=True, help_text="Whether this account can be used for payouts")
    is_default = models.BooleanField(default=False, help_text="Default account for payouts")
    
    # Verification Details
    verified_at = models.DateTimeField(null=True, blank=True, help_text="When this account was verified")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_bank_accounts', help_text="Admin who verified this account")
    verification_notes = models.TextField(blank=True, help_text="Admin notes about verification")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Provider Bank Account"
        verbose_name_plural = "Provider Bank Accounts"
        ordering = ['-is_default', '-created_at']
        unique_together = [
            ['provider', 'account_number', 'bank'],
            ['provider', 'account_name']
        ]
    
    def __str__(self):
        return f"{self.provider.email} - {self.account_name} ({self.get_bank_display()})"
    
    def get_bank_display_name(self):
        """Get the actual bank name"""
        if self.bank == 'other':
            return self.other_bank_name or 'Other Bank'
        return self.get_bank_display()
    
    def get_masked_account_number(self):
        """Return masked account number for security"""
        if len(self.account_number) <= 4:
            return '*' * len(self.account_number)
        return '*' * (len(self.account_number) - 4) + self.account_number[-4:]
    
    def verify(self, verified_by_user, notes=''):
        """Mark this account as verified"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.verified_by = verified_by_user
        self.verification_notes = notes
        self.save()
    
    def set_as_default(self):
        """Set this account as the default for the provider"""
        # Unset all other accounts for this provider
        ProviderBankAccount.objects.filter(provider=self.provider).update(is_default=False)
        # Set this one as default
        self.is_default = True
        self.save()
    
    def can_be_used_for_payout(self):
        """Check if this account can be used for payouts"""
        return self.is_active and self.is_verified
    
    @property
    def display_name(self):
        """Get formatted display name"""
        return f"{self.account_name} - {self.get_bank_display_name()} (****{self.account_number[-4:]})"


class PayoutRequest(models.Model):
    """
    Track payout requests made by providers
    """
    PAYOUT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('instant_payment', 'Instant Payment'),
        ('cash_send', 'Cash Send'),
        ('ewallet', 'E-Wallet'),
    ]
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('processing', 'Processing'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Request Details
    provider = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'service_provider'}, related_name='payout_requests')
    bank_account = models.ForeignKey(ProviderBankAccount, on_delete=models.CASCADE, related_name='payout_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount to be paid out")
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS, default='bank_transfer')
    
    # Status and Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    admin_notes = models.TextField(blank=True, help_text="Admin processing notes")
    transaction_reference = models.CharField(max_length=100, blank=True, help_text="Transaction reference number")
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.provider.email} - R{self.amount} - {self.get_status_display()}"
    
    def approve(self, admin_user, notes=''):
        """Approve this payout request"""
        self.status = 'approved'
        self.processed_at = timezone.now()
        self.admin_notes = notes
        self.save()
    
    def complete(self, transaction_ref='', notes=''):
        """Mark this payout as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.transaction_reference = transaction_ref
        if notes:
            self.admin_notes = notes
        self.save()
    
    def reject(self, admin_user, reason=''):
        """Reject this payout request"""
        self.status = 'rejected'
        self.processed_at = timezone.now()
        self.admin_notes = reason
        self.save()
