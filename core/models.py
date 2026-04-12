from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(email=username)


class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('homeowner', 'Homeowner'),
        ('service_provider', 'Service Provider'),
    ]
    
    username = None  
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='homeowner')
    
    # Basic Profile Fields
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Service Provider Specific Fields
    service_categories = models.ManyToManyField('gigs.Category', blank=True, help_text="Select service categories")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Rate per hour in local currency")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Rate per day in local currency")
    square_meter_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Rate per square meter for construction services")
    skills = models.TextField(blank=True, help_text="List of professional skills and qualifications")
    years_experience = models.PositiveIntegerField(null=True, blank=True, help_text="Years of professional experience")
    portfolio_description = models.TextField(blank=True, help_text="Description of portfolio and past work")
    references = models.TextField(blank=True, help_text="Professional references and testimonials")
    id_passport_number = models.CharField(max_length=50, blank=True, help_text="ID or Passport number for verification")
    is_verified = models.BooleanField(default=False, help_text="Whether the service provider has been verified")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email


class ProfessionalReference(models.Model):
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='professional_references')
    name = models.CharField(max_length=100, help_text="Reference person's name")
    contact = models.CharField(max_length=100, help_text="Reference contact information")
    type_of_work = models.CharField(max_length=200, help_text="Type of work performed")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reference for {self.service_provider.email} by {self.name}"


class Portfolio(models.Model):
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    project_url = models.URLField(blank=True, help_text="Link to project (if available)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.service_provider.email}"
    
    @property
    def primary_image(self):
        """Get the first image as primary image"""
        return self.images.first()
    
    @property
    def all_images(self):
        """Get all images for this portfolio item"""
        return self.images.all()


class PortfolioImage(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio_images/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Image for {self.portfolio.title}"


class WorkExperience(models.Model):
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_experiences')
    position = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='work_experience/', blank=True, null=True, help_text="Company logo or work image")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.position} at {self.company}"


# Import provider bank account models to ensure they're registered
from .models_provider_bank import ProviderBankAccount, PayoutRequest
