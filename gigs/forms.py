from django import forms
from django.utils import timezone
from .models import Gig, Category, Subcategory, GigPackage, GigRequirement, GigFAQ, GigGallery, QuotationRequest, QuotationResponse, JobApplication
from django.contrib.auth import get_user_model

User = get_user_model()


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'cover_letter', 'proposed_rate', 'estimated_duration', 
            'availability_start'
        ]
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Explain why you\'re the best fit for this job...', 'class': 'form-control'}),
            'proposed_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'estimated_duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3 days, 1 week'}),
            'availability_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_letter'].label = 'Cover Letter *'
        self.fields['proposed_rate'].label = 'Proposed Rate (R)'
        self.fields['estimated_duration'].label = 'Estimated Duration *'
        self.fields['availability_start'].label = 'Available to Start *'


class GigForm(forms.ModelForm):
    class Meta:
        model = Gig
        fields = [
            'title', 'description', 'category', 'subcategory',
            'budget_min', 'budget_max', 'location', 'start_date', 'end_date', 'urgency',
            'image', 'video', 'requires_approval', 'job_status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter job title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe the job in detail...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'subcategory': forms.Select(attrs={'class': 'form-select'}),
            'budget_min': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'budget_max': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job location'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'job_status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['subcategory'].queryset = Subcategory.objects.none()
        
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')


class GigPackageForm(forms.ModelForm):
    class Meta:
        model = GigPackage
        fields = ['name', 'title', 'description', 'price', 'delivery_days', 'revisions', 'features']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'features': forms.Textarea(attrs={'rows': 5, 'placeholder': 'One feature per line'}),
        }


class GigRequirementForm(forms.ModelForm):
    class Meta:
        model = GigRequirement
        fields = ['requirement', 'is_required']


class GigFAQForm(forms.ModelForm):
    class Meta:
        model = GigFAQ
        fields = ['question', 'answer']
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 3}),
        }


class GigGalleryForm(forms.ModelForm):
    class Meta:
        model = GigGallery
        fields = ['image', 'caption']


class QuotationRequestForm(forms.ModelForm):
    class Meta:
        model = QuotationRequest
        fields = ['category', 'title', 'description', 'location', 'start_date', 'end_date', 'budget_range', 'urgency', 'response_deadline']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief title for your job'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe what you need done...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where is the job located?'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., R500-R1000'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'response_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Select a category"
        self.fields['response_deadline'].label = "Response Deadline *"
        self.fields['response_deadline'].help_text = "Service providers must submit their quotes before this deadline"


class QuotationResponseForm(forms.ModelForm):
    # Additional fields for rate-based calculation
    calculation_method = forms.ChoiceField(
        choices=[
            ('hourly', 'Hourly Rate'),
            ('square_meter', 'Rate per Square Meter'),
            ('daily', 'Daily Rate'),
            ('fixed', 'Fixed Price')
        ],
        initial='fixed',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Quantity fields for rate calculations
    hours_required = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '0.0'})
    )
    
    square_meters_required = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': '0.0'})
    )
    
    days_required = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '0.0'})
    )
    
    class Meta:
        model = QuotationResponse
        fields = ['estimated_price', 'price_breakdown', 'estimated_duration', 'notes', 'availability']
        widgets = {
            'estimated_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'readonly': True}),
            'price_breakdown': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed breakdown of costs...'}),
            'estimated_duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3-5 days'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes or comments...'}),
            'availability': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your availability for this job...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['calculation_method'].label = 'Pricing Method'
        self.fields['hours_required'].label = 'Hours Required'
        self.fields['square_meters_required'].label = 'Square Meters Required'
        self.fields['days_required'].label = 'Days Required'
        self.fields['estimated_price'].label = 'Calculated Price (R)'
        self.fields['price_breakdown'].label = 'Price Breakdown'
        self.fields['estimated_duration'].label = 'Estimated Duration'
        self.fields['notes'].label = 'Additional Notes'
        self.fields['availability'].label = 'Availability'
    
    def clean(self):
        cleaned_data = super().clean()
        calculation_method = cleaned_data.get('calculation_method')
        
        if calculation_method == 'hourly':
            if not cleaned_data.get('hours_required'):
                self.add_error('hours_required', 'Hours required is mandatory for hourly pricing')
        elif calculation_method == 'square_meter':
            if not cleaned_data.get('square_meters_required'):
                self.add_error('square_meters_required', 'Square meters required is mandatory for square meter pricing')
        elif calculation_method == 'daily':
            if not cleaned_data.get('days_required'):
                self.add_error('days_required', 'Days required is mandatory for daily pricing')
        
        return cleaned_data


class ProviderSelectionForm(forms.Form):
    providers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text="Select all providers you want to request quotations from"
    )
    
    def __init__(self, category, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if category:
            self.fields['providers'].queryset = User.objects.filter(
                user_type='service_provider',
                service_categories=category
            ).order_by('email')
        else:
            self.fields['providers'].queryset = User.objects.filter(
                user_type='service_provider'
            ).order_by('email')
        
        self.fields['providers'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.email}"


class QuotationRequestWithProvidersForm(forms.ModelForm):
    providers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text="Select all providers you want to request quotations from"
    )
    
    class Meta:
        model = QuotationRequest
        fields = ['category', 'title', 'description', 'location', 'start_date', 'end_date', 'budget_range', 'urgency', 'response_deadline']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief title for your job'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe what you need done...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where is the job located?'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., R500-R1000'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'response_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Select a category"
        self.fields['response_deadline'].label = "Response Deadline *"
        self.fields['response_deadline'].help_text = "Service providers must submit their quotes before this deadline"
        
        # Only show verified service providers or those with complete profiles
        self.fields['providers'].queryset = User.objects.filter(
            user_type='service_provider'
        ).order_by('email')
        self.fields['providers'].help_text = "Select specific service providers to send this quotation request to. Only selected providers will see and be able to respond to your request."
        self.fields['providers'].label_from_instance = lambda obj: f"{obj.get_full_name() or obj.email}"


class UpdateQuotationRequestForm(forms.ModelForm):
    """Form for updating existing quotation requests"""
    
    class Meta:
        model = QuotationRequest
        fields = ['category', 'title', 'description', 'location', 'start_date', 'end_date', 'budget_range', 'urgency', 'response_deadline']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief title for your job'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe what you need done...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where is the job located?'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'budget_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., R500-R1000'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'response_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Select a category"
        self.fields['response_deadline'].label = "Response Deadline"
        self.fields['response_deadline'].help_text = "Service providers must submit their quotes before this deadline"
        
        # Set field labels
        self.fields['category'].label = "Category *"
        self.fields['title'].label = "Job Title *"
        self.fields['description'].label = "Job Description *"
        self.fields['location'].label = "Location *"
        self.fields['start_date'].label = "Start Date"
        self.fields['end_date'].label = "End Date"
        self.fields['budget_range'].label = "Budget Range"
        self.fields['urgency'].label = "Urgency *"
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        response_deadline = cleaned_data.get('response_deadline')
        
        # Validate date logic
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date")
        
        # Validate deadline is in future
        if response_deadline and response_deadline <= timezone.now():
            raise forms.ValidationError("Response deadline must be in the future")
        
        return cleaned_data
