from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
# from taggit.managers import TaggableManager  # Temporarily disabled

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Subcategories"
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Gig(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, null=True, blank=True)
    # tags = TaggableManager()  # Temporarily disabled
    
    # Job details
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True, help_text="Expected start date for the job")
    end_date = models.DateField(null=True, blank=True, help_text="Expected completion date for the job")
    urgency = models.CharField(max_length=20, choices=[
        ('asap', 'ASAP'),
        ('within_week', 'Within a week'),
        ('within_month', 'Within a month'),
        ('flexible', 'Flexible'),
    ], default='flexible')
    
    # Job settings
    image = models.ImageField(upload_to='job_images/', blank=True, null=True)
    video = models.FileField(upload_to='job_videos/', blank=True, null=True)
    requires_approval = models.BooleanField(default=False)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)  # Private jobs only visible to hired provider
    hired_provider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hired_jobs')
    job_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ], default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.homeowner.email}"


class QuotationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('receiving_responses', 'Receiving Responses'),
        ('evaluation_period', 'Evaluation Period'),
        ('provider_selected', 'Provider Selected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotation_requests')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    budget_range = models.CharField(max_length=100, blank=True, help_text="Optional budget range")
    urgency = models.CharField(max_length=20, choices=[
        ('asap', 'ASAP'),
        ('within_week', 'Within a week'),
        ('within_month', 'Within a month'),
        ('flexible', 'Flexible'),
    ], default='flexible')
    
    # Deadline for provider responses
    response_deadline = models.DateTimeField(null=True, blank=True, help_text="Deadline for service providers to submit their quotes")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    selected_provider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_quotations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.homeowner.email}"
    
    def is_response_deadline_passed(self):
        """Check if the response deadline has passed"""
        from django.utils import timezone
        return timezone.now() > self.response_deadline
    
    def can_receive_responses(self):
        """Check if the quotation request can still receive responses"""
        return self.status == 'receiving_responses' and not self.is_response_deadline_passed()


class QuotationResponse(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    quotation_request = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE, related_name='responses')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotation_responses')
    
    # Pricing details
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_breakdown = models.TextField(help_text="Detailed breakdown of costs")
    estimated_duration = models.CharField(max_length=100, help_text="How long the job will take")
    
    # Provider notes
    notes = models.TextField(blank=True, help_text="Additional notes or comments")
    availability = models.TextField(help_text="Provider availability for this job")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['quotation_request', 'service_provider']
        ordering = ['estimated_price']
    
    def __str__(self):
        return f"{self.service_provider.email} - {self.quotation_request.title}"


class QuotationRequestProvider(models.Model):
    """Track which providers were sent each quotation request"""
    quotation_request = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE, related_name='sent_providers')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_quotations')
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['quotation_request', 'service_provider']
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.quotation_request.title} sent to {self.service_provider.email}"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='applications')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    
    # Application details
    cover_letter = models.TextField(help_text="Why you're the best fit for this job")
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Your proposed rate")
    estimated_duration = models.CharField(max_length=100, help_text="How long you estimate the job will take")
    availability_start = models.DateField(null=True, blank=True, help_text="When you're available to start")
    portfolio_links = models.TextField(blank=True, help_text="Links to relevant portfolio items")
    
    # Application status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-applied_at']
        unique_together = ['gig', 'service_provider']
    
    def __str__(self):
        return f"{self.service_provider.email} - {self.gig.title}"


class GigPackage(models.Model):
    PACKAGE_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=50, choices=PACKAGE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    delivery_days = models.PositiveIntegerField()
    revisions = models.PositiveIntegerField(default=1)
    features = models.TextField(help_text="One feature per line")
    
    class Meta:
        unique_together = ['gig', 'name']
    
    def __str__(self):
        return f"{self.gig.title} - {self.get_name_display()}"
    
    def get_features_list(self):
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]


class GigRequirement(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='requirements')
    requirement = models.CharField(max_length=200)
    is_required = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.gig.title} - {self.requirement}"


class GigFAQ(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=300)
    answer = models.TextField()
    
    def __str__(self):
        return f"{self.gig.title} - {self.question}"


class GigGallery(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='gig_gallery/')
    caption = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.gig.title} - Gallery Image"
