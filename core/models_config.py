"""
System configuration models for managing platform settings
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings managed by administrators
    """
    CONFIG_TYPES = [
        ('payment', 'Payment Settings'),
        ('email', 'Email Settings'),
        ('platform', 'Platform Settings'),
        ('whatsapp', 'WhatsApp Settings'),
        ('fees', 'Fee Settings'),
        ('banking', 'Banking Settings'),
    ]
    
    key = models.CharField(max_length=100, unique=True, help_text="Configuration key")
    value = models.TextField(help_text="Configuration value (JSON for complex data)")
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='platform')
    description = models.TextField(blank=True, help_text="Description of this configuration")
    is_active = models.BooleanField(default=True, help_text="Whether this configuration is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"
        ordering = ['config_type', 'key']
    
    def __str__(self):
        return f"{self.config_type}: {self.key}"
    
    def get_value(self):
        """Get parsed value (JSON or string)"""
        try:
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value
    
    def set_value(self, value):
        """Set value (auto-serialize to JSON if needed)"""
        if isinstance(value, (dict, list, bool, int, float)):
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class BankAccount(models.Model):
    """
    Bank account details for EFT payments - managed by system admin
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
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, help_text="Account name/label")
    bank = models.CharField(max_length=20, choices=BANKS, help_text="Bank name")
    other_bank_name = models.CharField(max_length=100, blank=True, help_text="Specify if 'Other' bank selected")
    account_holder_name = models.CharField(max_length=100, help_text="Full name of account holder")
    account_number = models.CharField(max_length=20, help_text="Bank account number")
    branch_code = models.CharField(max_length=10, help_text="6-digit branch code")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='cheque')
    is_active = models.BooleanField(default=True, help_text="Whether this account is active for payments")
    is_default = models.BooleanField(default=False, help_text="Default account for EFT payments")
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum payment amount")
    maximum_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum payment amount (leave blank for unlimited)")
    notes = models.TextField(blank=True, help_text="Additional notes about this account")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_bank_display()}"
    
    def get_bank_display_name(self):
        """Get the actual bank name"""
        if self.bank == 'other':
            return self.other_bank_name or 'Other Bank'
        return self.get_bank_display()
    
    def clean(self):
        """Validate that only one account can be default"""
        if self.is_default:
            BankAccount.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)


class PaymentMethod(models.Model):
    """
    Available payment methods and their configurations
    """
    METHOD_TYPES = [
        ('yoco', 'Yoco (Mobile Card Payments)'),
        ('ozow', 'Ozow (Instant EFT)'),
        ('eft', 'EFT Transfer'),
        ('in_person', 'In-Person Payment'),
    ]
    
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES, unique=True)
    name = models.CharField(max_length=100, help_text="Display name for this payment method")
    description = models.TextField(help_text="Description shown to users")
    is_active = models.BooleanField(default=True, help_text="Whether this payment method is available")
    icon_class = models.CharField(max_length=50, help_text="Font Awesome icon class (e.g., 'fas fa-credit-card')")
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Transaction fee percentage")
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Fixed transaction fee")
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum payment amount")
    maximum_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum payment amount")
    processing_time = models.CharField(max_length=50, default="Instant", help_text="Expected processing time")
    instructions = models.TextField(blank=True, help_text="Special instructions for this payment method")
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def calculate_fees(self, amount):
        """Calculate total fees for a given amount"""
        percentage_fee = amount * (self.fee_percentage / 100)
        total_fee = percentage_fee + self.fee_fixed
        return total_fee
    
    def is_amount_valid(self, amount):
        """Check if amount is within valid range"""
        if amount < self.minimum_amount:
            return False
        if self.maximum_amount and amount > self.maximum_amount:
            return False
        return True


class PlatformFee(models.Model):
    """
    Platform fee structure for transactions
    """
    FEE_TYPES = [
        ('commission', 'Commission Fee'),
        ('service_fee', 'Service Fee'),
        ('transaction_fee', 'Transaction Fee'),
        ('withdrawal_fee', 'Withdrawal Fee'),
    ]
    
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, unique=True)
    name = models.CharField(max_length=100, help_text="Display name for this fee")
    description = models.TextField(help_text="Description of what this fee covers")
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Fee percentage")
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Fixed fee amount")
    is_active = models.BooleanField(default=True, help_text="Whether this fee is currently active")
    applies_to = models.CharField(max_length=50, help_text="Who this fee applies to (e.g., 'service_provider', 'homeowner', 'both')")
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum amount for fee to apply")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Platform Fee"
        verbose_name_plural = "Platform Fees"
        ordering = ['fee_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_fee_type_display()})"
    
    def calculate_fee(self, amount):
        """Calculate fee for a given amount"""
        if amount < self.minimum_amount:
            return 0
        
        percentage_fee = amount * (self.fee_percentage / 100)
        total_fee = percentage_fee + self.fee_fixed
        return total_fee


class EmailConfiguration(models.Model):
    """
    Email configuration settings
    """
    CONFIG_TYPES = [
        ('smtp', 'SMTP Settings'),
        ('sendgrid', 'SendGrid Settings'),
        ('ses', 'AWS SES Settings'),
        ('mailgun', 'Mailgun Settings'),
    ]
    
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES)
    is_active = models.BooleanField(default=False, help_text="Whether this email configuration is active")
    host = models.CharField(max_length=255, blank=True, help_text="SMTP host")
    port = models.PositiveIntegerField(null=True, blank=True, help_text="SMTP port")
    username = models.CharField(max_length=255, blank=True, help_text="SMTP username")
    password = models.CharField(max_length=255, blank=True, help_text="SMTP password")
    use_tls = models.BooleanField(default=True, help_text="Use TLS encryption")
    use_ssl = models.BooleanField(default=False, help_text="Use SSL encryption")
    from_email = models.EmailField(help_text="Default from email address")
    from_name = models.CharField(max_length=100, help_text="Default from name")
    api_key = models.CharField(max_length=255, blank=True, help_text="API key for service-based email providers")
    domain = models.CharField(max_length=255, blank=True, help_text="Domain for service-based email providers")
    daily_limit = models.PositiveIntegerField(default=1000, help_text="Daily email sending limit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Email Configuration"
        verbose_name_plural = "Email Configurations"
        ordering = ['-is_active', 'config_type']
    
    def __str__(self):
        return f"{self.get_config_type_display()} ({'Active' if self.is_active else 'Inactive'})"
    
    def clean(self):
        """Ensure only one configuration is active"""
        if self.is_active:
            EmailConfiguration.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
