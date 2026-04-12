from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from gigs.models import Category

User = get_user_model()

class CustomSignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    password2 = forms.CharField(
        label="Confirm Password", 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )
    service_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'user_type', 'phone', 'location',
            'bio', 'hourly_rate', 'square_meter_rate', 'years_experience',
            'skills', 'portfolio_description', 'service_categories'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City/Area'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '50.00'}),
            'square_meter_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '100.00'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '5'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your skills...'}),
            'portfolio_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your experience...'}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['user_type'].widget = forms.Select(
            choices=User.USER_TYPE_CHOICES,
            attrs={'class': 'form-control'}
        )
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        return password2
    
    def clean_hourly_rate(self):
        hourly_rate = self.cleaned_data.get('hourly_rate')
        user_type = self.cleaned_data.get('user_type')
        
        if user_type == 'service_provider' and (not hourly_rate or hourly_rate <= 0):
            raise forms.ValidationError('Hourly rate is required and must be greater than 0 for service providers.')
        return hourly_rate
    
    def clean_service_categories(self):
        service_categories = self.cleaned_data.get('service_categories')
        user_type = self.cleaned_data.get('user_type')
        
        if user_type == 'service_provider' and not service_categories:
            raise forms.ValidationError('Please select at least one service category.')
        return service_categories
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if user_type == 'service_provider':
            required_fields = ['phone', 'location', 'skills', 'bio']
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f'This field is required for service providers.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.username = user.email  # Set username to email
        
        if commit:
            user.save()
            # Handle ManyToMany field
            if user.user_type == 'service_provider':
                service_categories = self.cleaned_data.get('service_categories')
                if service_categories:
                    user.service_categories.set(service_categories)
        
        return user
