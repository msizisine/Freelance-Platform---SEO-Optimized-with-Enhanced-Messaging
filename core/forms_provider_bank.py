"""
Forms for provider bank account management
"""

from django import forms
from django.core.exceptions import ValidationError
from .models_provider_bank import ProviderBankAccount, PayoutRequest


class ProviderBankAccountForm(forms.ModelForm):
    """Form for providers to add/edit their bank accounts"""
    
    class Meta:
        model = ProviderBankAccount
        fields = [
            'account_name', 'bank', 'other_bank_name', 'account_holder_name',
            'account_number', 'branch_code', 'account_type'
        ]
        widgets = {
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., My Main Account'
            }),
            'bank': forms.Select(attrs={'class': 'form-select'}),
            'other_bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bank name if "Other" selected'
            }),
            'account_holder_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name as it appears on bank account'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account number (digits only)',
                'pattern': '[0-9]+',
                'minlength': '6',
                'maxlength': '20'
            }),
            'branch_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '6-digit branch code',
                'pattern': '[0-9]{6}',
                'minlength': '6',
                'maxlength': '6'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)
        
        # Make other_bank_name required if bank is 'other'
        self.fields['other_bank_name'].required = False
        
        # Add help text
        self.fields['account_number'].help_text = "Enter your bank account number (digits only)"
        self.fields['branch_code'].help_text = "Enter the 6-digit branch code"
        
        # Add field labels
        self.fields['account_name'].label = "Account Name"
        self.fields['bank'].label = "Bank"
        self.fields['other_bank_name'].label = "Other Bank Name"
        self.fields['account_holder_name'].label = "Account Holder Name"
        self.fields['account_number'].label = "Account Number"
        self.fields['branch_code'].label = "Branch Code"
        self.fields['account_type'].label = "Account Type"
    
    def clean_account_number(self):
        """Validate account number"""
        account_number = self.cleaned_data.get('account_number')
        if not account_number.isdigit():
            raise ValidationError("Account number must contain only digits")
        if len(account_number) < 6:
            raise ValidationError("Account number must be at least 6 digits")
        return account_number
    
    def clean_branch_code(self):
        """Validate branch code"""
        branch_code = self.cleaned_data.get('branch_code')
        if not branch_code.isdigit():
            raise ValidationError("Branch code must contain only digits")
        if len(branch_code) != 6:
            raise ValidationError("Branch code must be exactly 6 digits")
        return branch_code
    
    def clean(self):
        """Clean form data and check for duplicates"""
        cleaned_data = super().clean()
        bank = cleaned_data.get('bank')
        other_bank_name = cleaned_data.get('other_bank_name')
        
        # Validate other bank name if 'other' is selected
        if bank == 'other' and not other_bank_name:
            raise ValidationError("Please specify the bank name when 'Other' is selected")
        
        # Check for duplicate account numbers for the same provider and bank
        if self.provider and not self.instance.pk:  # Only for new accounts
            account_number = cleaned_data.get('account_number')
            if ProviderBankAccount.objects.filter(
                provider=self.provider,
                account_number=account_number,
                bank=bank
            ).exists():
                raise ValidationError("You already have an account with this number for this bank")
        
        return cleaned_data


class PayoutRequestForm(forms.ModelForm):
    """Form for providers to request payouts"""
    
    class Meta:
        model = PayoutRequest
        fields = ['bank_account', 'amount', 'payout_method']
        widgets = {
            'bank_account': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '50.00'
            }),
            'payout_method': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)
        
        if self.provider:
            # Only show verified and active bank accounts
            self.fields['bank_account'].queryset = ProviderBankAccount.objects.filter(
                provider=self.provider,
                is_active=True,
                is_verified=True
            )
        
        # Add field labels and help text
        self.fields['bank_account'].label = "Bank Account"
        self.fields['bank_account'].help_text = "Select your verified bank account for payout"
        self.fields['amount'].label = "Payout Amount (R)"
        self.fields['amount'].help_text = "Minimum payout amount is R50.00"
        self.fields['payout_method'].label = "Payout Method"
        self.fields['payout_method'].help_text = "Choose how you want to receive your payment"
    
    def clean_amount(self):
        """Validate payout amount"""
        amount = self.cleaned_data.get('amount')
        if amount < 50:
            raise ValidationError("Minimum payout amount is R50.00")
        
        # Check if provider has sufficient available earnings
        if self.provider:
            from .models_payments import ProviderEarnings
            available_earnings = ProviderEarnings.objects.filter(
                provider=self.provider,
                status='available'
            ).aggregate(total=models.Sum('net_amount'))['total'] or 0
            
            if amount > available_earnings:
                raise ValidationError(f"Insufficient available earnings. You have R{available_earnings:.2f} available.")
        
        return amount


class BankAccountVerificationForm(forms.ModelForm):
    """Form for admins to verify bank accounts"""
    
    class Meta:
        model = ProviderBankAccount
        fields = ['verification_notes']
        widgets = {
            'verification_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add verification notes...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['verification_notes'].label = "Verification Notes"
        self.fields['verification_notes'].help_text = "Add any notes about this verification"
