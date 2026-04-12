"""
Forms for provider payment processing
"""

from django import forms
from django.core.exceptions import ValidationError
from ..models_payments import ProviderPayout, PAYOUT_METHODS, PRIORITY_CHOICES


class PayoutRequestForm(forms.ModelForm):
    """Form for creating payout requests"""
    
    class Meta:
        model = ProviderPayout
        fields = ['gross_amount', 'payout_method', 'priority', 'recipient_name', 
                'recipient_phone', 'recipient_email', 'bank_account', 'bank_name', 'branch_code', 'notes']
        widgets = {
            'gross_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '10.00'
            }),
            'payout_method': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name'
            }),
            'recipient_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+27 12 345 6789'
            }),
            'recipient_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'bank_account': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account number'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank name'
            }),
            'branch_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Branch code'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gross_amount'].label = 'Total Amount to Payout'
        self.fields['payout_method'].label = 'Payout Method'
        self.fields['priority'].label = 'Processing Priority'
        self.fields['recipient_name'].label = 'Recipient Full Name'
        self.fields['recipient_phone'].label = 'Recipient Phone Number'
        self.fields['recipient_email'].label = 'Recipient Email Address'
        self.fields['bank_account'].label = 'Bank Account Number'
        self.fields['bank_name'].label = 'Bank Name'
        self.fields['branch_code'].label = 'Branch Code'
        self.fields['notes'].label = 'Notes'
    
    def clean(self):
        cleaned_data = super().clean()
        payout_method = cleaned_data.get('payout_method')
        priority = cleaned_data.get('priority')
        
        # Validate required fields based on payout method
        if payout_method == 'bank_transfer':
            if not cleaned_data.get('bank_account'):
                raise ValidationError('Bank account number is required for bank transfers.')
            if not cleaned_data.get('bank_name'):
                raise ValidationError('Bank name is required for bank transfers.')
            if not cleaned_data.get('branch_code'):
                raise ValidationError('Branch code is required for bank transfers.')
        
        elif payout_method == 'ewallet':
            if not cleaned_data.get('recipient_email'):
                raise ValidationError('Email address is required for e-wallet payments.')
        
        elif payout_method in ['cash_send', 'payshap']:
            if not cleaned_data.get('recipient_phone'):
                raise ValidationError('Phone number is required for mobile payments.')
        
        # Validate minimum amount
        gross_amount = cleaned_data.get('gross_amount')
        if gross_amount and gross_amount < 10:
            raise ValidationError('Minimum payout amount is R10.00.')
        
        return cleaned_data


class PayoutApprovalForm(forms.Form):
    """Form for admin to approve payouts"""
    
    transaction_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter transaction ID'
        })
    )
    
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Admin notes...'
        })
    )


class PayoutCompletionForm(forms.Form):
    """Form for admin to mark payouts as completed"""
    
    receipt_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://...'
        })
    )


class PayoutRejectionForm(forms.Form):
    """Form for admin to reject payouts"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Reason for rejection...',
            'required': True
        })
    )


class EarningsSelectionForm(forms.Form):
    """Form for selecting earnings to include in payout"""
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Get available earnings
        from ..models_payments import ProviderEarnings
        available_earnings = ProviderEarnings.objects.filter(
            provider=user,
            status='available'
        ).order_by('-created_at')
        
        # Create choices for earnings selection
        choices = []
        for earning in available_earnings:
            amount_str = f"R{earning.net_amount} - {earning.get_earning_type_display()} - {earning.created_at.strftime('%Y-%m-%d')}"
            choices.append((str(earning.id), amount_str))
        
        self.fields['selected_earnings'] = forms.MultipleChoiceField(
            choices=choices,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            required=True,
            label='Select Earnings to Payout'
        )
    
    def clean_selected_earnings(self):
        selected_ids = self.cleaned_data.get('selected_earnings')
        if not selected_ids:
            raise ValidationError('Please select at least one earning to payout.')
        return selected_ids
