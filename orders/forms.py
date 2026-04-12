from django import forms
from django.contrib.auth import get_user_model
from .models import Order, OrderMessage, OrderRevision, JobOffer
from gigs.models import Gig, Category

User = get_user_model()


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['gig', 'requirements', 'total_amount', 'due_date']
        widgets = {
            'requirements': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your requirements for this order...'}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gig'].queryset = Gig.objects.filter(is_active=True)
        
    def clean(self):
        cleaned_data = super().clean()
        gig = cleaned_data.get('gig')
        if gig:
            # For home services, we don't have packages, so we'll use the gig's budget
            if not cleaned_data.get('total_amount'):
                cleaned_data['total_amount'] = gig.budget_max
            cleaned_data['delivery_days'] = 7  # Default delivery time
            
        return cleaned_data


class JobCreationForm(forms.Form):
    """Form for homeowners to create new jobs"""
    
    job_title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a descriptive job title...'}),
        required=True
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a category...",
        required=True
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your job in detail...'}),
        required=True
    )
    
    location = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job location (e.g., Johannesburg, Sandton...)'}),
        required=False
    )
    
    budget_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum budget (R)', 'step': '0.01', 'min': '0'}),
        required=False
    )
    
    budget_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum budget (R)', 'step': '0.01', 'min': '0'}),
        required=True
    )
    
    urgency = forms.ChoiceField(
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='medium',
        required=False
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    completion_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    
    job_images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Upload images to help professionals understand your job (optional)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')
        start_date = cleaned_data.get('start_date')
        completion_date = cleaned_data.get('completion_date')
        
        if budget_min and budget_max and budget_min > budget_max:
            raise forms.ValidationError("Minimum budget cannot be greater than maximum budget.")
        
        if start_date and completion_date and start_date > completion_date:
            raise forms.ValidationError("Start date cannot be after completion date.")
        
        return cleaned_data


class OrderMessageForm(forms.ModelForm):
    class Meta:
        model = OrderMessage
        fields = ['message', 'file_attachment']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...', 'class': 'form-control'}),
            'file_attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


class OrderRevisionForm(forms.ModelForm):
    class Meta:
        model = OrderRevision
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please explain what needs to be revised...'}),
        }


class JobOfferForm(forms.ModelForm):
    """Form for creating job offers"""
    
    class Meta:
        model = JobOffer
        fields = ['job_title', 'job_description', 'budget_min', 'budget_max']
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your job requirements...'}),
            'budget_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum Budget', 'step': '0.01'}),
            'budget_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum Budget', 'step': '0.01'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')
        
        if budget_min and budget_max and budget_min > budget_max:
            raise forms.ValidationError("Minimum budget cannot be greater than maximum budget.")
        
        return cleaned_data


class PrivateJobForm(forms.Form):
    """Dedicated form for creating private jobs"""
    
    def __init__(self, *args, **kwargs):
        provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)
        
        if provider:
            self.fields['category'].queryset = provider.service_categories.all()
    
    job_title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Title'}),
        required=True
    )
    budget_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum Budget', 'step': '0.01'}),
        required=False
    )
    budget_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maximum Budget', 'step': '0.01'}),
        required=False
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    completion_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False
    )
    requirements = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your job requirements...'}),
        required=True
    )
    category = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        empty_label="Select a category"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')
        
        if budget_min and budget_max and budget_min > budget_max:
            raise forms.ValidationError("Minimum budget cannot be greater than maximum budget.")
        
        return cleaned_data


class JobEstimateForm(forms.ModelForm):
    """Form for service providers to submit estimates"""
    
    DURATION_CHOICES = [
        ('1 day', '1 day'),
        ('1 week', '1 week'),
        ('2 weeks', '2 weeks'),
        ('1 month', '1 month'),
    ]
    
    RATE_TYPE_CHOICES = [
        ('hourly', 'Hourly Rate'),
        ('daily', 'Daily Rate'),
        ('square_meter', 'Square Meter Rate'),
    ]
    
    rate_type = forms.ChoiceField(
        choices=RATE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'rate_type_select'}),
        required=True,
        label='Rate Type'
    )
    
    estimated_duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'duration_select'}),
        required=True
    )
    
    square_meters = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Square meters', 'step': '0.01', 'id': 'square_meters_input'}),
        required=False,
        help_text="Required only when using square meter rate"
    )
    
    class Meta:
        model = JobOffer
        fields = ['estimated_price', 'estimated_duration', 'estimate_description']
        widgets = {
            'estimated_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Calculated Price', 'step': '0.01', 'readonly': True, 'id': 'calculated_price'}),
            'estimate_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your approach and what\'s included in your estimate...'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.service_provider = kwargs.pop('service_provider', None)
        super().__init__(*args, **kwargs)
        
        if self.service_provider:
            # Set initial rate type based on available rates
            if self.service_provider.hourly_rate:
                self.fields['rate_type'].initial = 'hourly'
            elif self.service_provider.daily_rate:
                self.fields['rate_type'].initial = 'daily'
            elif self.service_provider.square_meter_rate:
                self.fields['rate_type'].initial = 'square_meter'
    
    def calculate_estimated_price(self, cleaned_data):
        """Calculate estimated price based on rate type and duration"""
        rate_type = cleaned_data.get('rate_type')
        duration = cleaned_data.get('estimated_duration')
        square_meters = cleaned_data.get('square_meters')
        
        if not rate_type or not duration:
            return None
        
        # Convert duration to days/weeks/months
        if duration == '1 day':
            days = 1
        elif duration == '1 week':
            days = 7
        elif duration == '2 weeks':
            days = 14
        elif duration == '1 month':
            days = 30  # Approximate
        else:
            days = 1
        
        # Calculate based on rate type
        if rate_type == 'hourly':
            hourly_rate = self.service_provider.hourly_rate
            if hourly_rate:
                # Assume 8 working hours per day
                total_hours = days * 8
                return hourly_rate * total_hours
        elif rate_type == 'daily':
            daily_rate = self.service_provider.daily_rate
            if daily_rate:
                return daily_rate * days
        elif rate_type == 'square_meter':
            square_meter_rate = self.service_provider.square_meter_rate
            if square_meter_rate and square_meters:
                return square_meter_rate * square_meters
        
        return None
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Calculate estimated price
        calculated_price = self.calculate_estimated_price(cleaned_data)
        if calculated_price:
            cleaned_data['estimated_price'] = calculated_price
        else:
            raise forms.ValidationError("Unable to calculate price. Please ensure you have set the appropriate rates in your profile.")
        
        # Validate square meters if using square meter rate
        if cleaned_data.get('rate_type') == 'square_meter':
            square_meters = cleaned_data.get('square_meters')
            if not square_meters or square_meters <= 0:
                raise forms.ValidationError("Square meters must be specified when using square meter rate.")
        
        return cleaned_data
