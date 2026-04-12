from django import forms
from django.contrib.auth import get_user_model
from core.models import ProfessionalReference, Portfolio, WorkExperience
from .phone_utils import validate_phone_number, format_for_whatsapp

User = get_user_model()

class ServiceProviderProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'location', 'bio',
            'service_categories', 'hourly_rate', 'daily_rate', 'square_meter_rate', 'skills',
            'years_experience', 'portfolio_description', 'references',
            'id_passport_number', 'profile_picture'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about your professional background...', 'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List your professional skills and qualifications...', 'class': 'form-control'}),
            'portfolio_description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your portfolio and past work experience...', 'class': 'form-control'}),
            'references': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Provide professional references and testimonials...', 'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '50.00', 'class': 'form-control'}),
            'daily_rate': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '400.00', 'class': 'form-control'}),
            'square_meter_rate': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '100.00', 'class': 'form-control'}),
            'years_experience': forms.NumberInput(attrs={'min': '0', 'placeholder': '5', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'id_passport_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone': 'Contact Number',
            'location': 'Service Area',
            'bio': 'Professional Bio',
            'service_categories': 'Service Categories',
            'hourly_rate': 'Hourly Rate (R)',
            'daily_rate': 'Daily Rate (R)',
            'square_meter_rate': 'Rate per Square Meter (R)',
            'skills': 'Skills & Qualifications',
            'years_experience': 'Years of Experience',
            'portfolio_description': 'Portfolio & Experience',
            'references': 'Professional References',
            'id_passport_number': 'ID/Passport Number',
            'profile_picture': 'Profile Picture',
        }
    
    def clean_service_categories(self):
        service_categories = self.cleaned_data.get('service_categories')
        # Remove validation since it's now a ManyToMany field
        return service_categories
    
    def clean_hourly_rate(self):
        hourly_rate = self.cleaned_data.get('hourly_rate')
        if hourly_rate is not None and hourly_rate <= 0:
            raise forms.ValidationError('Hourly rate must be greater than 0.')
        return hourly_rate
    
    def clean_square_meter_rate(self):
        square_meter_rate = self.cleaned_data.get('square_meter_rate')
        if square_meter_rate is not None and square_meter_rate <= 0:
            raise forms.ValidationError('Square meter rate must be greater than 0.')
        return square_meter_rate
    
    def clean_daily_rate(self):
        daily_rate = self.cleaned_data.get('daily_rate')
        if daily_rate is not None and daily_rate <= 0:
            raise forms.ValidationError('Daily rate must be greater than 0.')
        return daily_rate
    
    def clean_phone(self):
        """Clean and validate phone number"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Validate and format the phone number
            is_valid, formatted, error = validate_phone_number(phone)
            
            if not is_valid:
                raise forms.ValidationError(error)
            
            # Return the formatted number for WhatsApp compatibility
            return formatted
        
        return phone


class ProfessionalReferenceForm(forms.ModelForm):
    class Meta:
        model = ProfessionalReference
        fields = ['name', 'contact', 'type_of_work']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference person name'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number or email'}),
            'type_of_work': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the type of work performed...'}),
        }
        labels = {
            'name': 'Reference Name',
            'contact': 'Contact Information',
            'type_of_work': 'Type of Work Performed',
        }


class MultipleFileInput(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = 'multiple'
        attrs['class'] = 'form-control'
        attrs_str = ' '.join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<input type="file" name="{name}" {attrs_str}>'

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class PortfolioForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False,
        label='Project Images'
    )
    
    class Meta:
        model = Portfolio
        fields = ['title', 'description', 'project_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your project...'}),
            'project_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/project'}),
        }
        labels = {
            'title': 'Project Title',
            'description': 'Project Description',
            'project_url': 'Project URL (optional)',
        }


class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['position', 'company', 'start_date', 'end_date', 'description', 'image']
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job title'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your role and responsibilities...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'position': 'Position',
            'company': 'Company',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'description': 'Description',
            'image': 'Company/Work Image',
        }


class HomeownerProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'location', 'bio',
            'profile_picture'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0837009708'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone': 'Contact Number (WhatsApp)',
            'location': 'Service Area',
            'bio': 'About Me',
            'profile_picture': 'Profile Picture',
        }
    
    def clean_phone(self):
        """Clean and validate phone number"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Validate and format the phone number
            is_valid, formatted, error = validate_phone_number(phone)
            
            if not is_valid:
                raise forms.ValidationError(error)
            
            # Return the formatted number for WhatsApp compatibility
            return formatted
        
        return phone
