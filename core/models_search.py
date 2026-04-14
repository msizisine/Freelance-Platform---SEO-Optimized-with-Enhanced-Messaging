from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class SavedSearch(models.Model):
    """User saved search queries"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    query = models.TextField(help_text="URL query parameters")
    url = models.URLField(max_length=500)
    email_notifications = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(null=True, blank=True)
    new_results_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Saved Search"
        verbose_name_plural = "Saved Searches"

    def __str__(self):
        return f"{self.user.email} - {self.name}"

    def get_search_params(self):
        """Parse query string into dictionary"""
        from urllib.parse import parse_qs
        return parse_qs(self.query)


class SearchHistory(models.Model):
    """Track user search history for recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255)
    filters = models.JSONField(default=dict, help_text="Applied filters")
    results_count = models.PositiveIntegerField(default=0)
    clicked_results = models.JSONField(default=list, help_text="IDs of clicked results")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Search History"
        verbose_name_plural = "Search History"

    def __str__(self):
        return f"{self.user.email} - {self.query}"


class ProviderProfile(models.Model):
    """Extended profile for service providers with location and availability"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    
    # Location
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Availability
    is_available_now = models.BooleanField(default=False)
    is_available_today = models.BooleanField(default=False)
    is_available_this_week = models.BooleanField(default=True)
    available_hours_start = models.TimeField(null=True, blank=True)
    available_hours_end = models.TimeField(null=True, blank=True)
    available_days = models.JSONField(
        default=list, 
        help_text="Days of week available: [0,1,2,3,4,5,6] where 0=Monday"
    )
    
    # Service areas
    service_radius = models.PositiveIntegerField(
        default=25, 
        help_text="Service radius in kilometers",
        validators=[MinValueValidator(1), MaxValueValidator(200)]
    )
    service_areas = models.JSONField(
        default=list, 
        help_text="List of areas/suburbs served"
    )
    
    # Ratings and stats
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.PositiveIntegerField(default=0)
    job_count = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Response time
    average_response_time = models.PositiveIntegerField(
        default=60, 
        help_text="Average response time in minutes"
    )
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    id_verified = models.BooleanField(default=False)
    background_checked = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Provider Profile"
        verbose_name_plural = "Provider Profiles"

    def __str__(self):
        return f"{self.user.email} Profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_distance_to(self, latitude, longitude):
        """Calculate distance to a given point using Haversine formula"""
        if not self.latitude or not self.longitude or not latitude or not longitude:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1 = radians(float(self.latitude)), radians(float(self.longitude))
        lat2, lon2 = radians(float(latitude)), radians(float(longitude))
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r

    def is_in_service_area(self, latitude, longitude):
        """Check if a location is within service radius"""
        distance = self.get_distance_to(latitude, longitude)
        return distance <= self.service_radius if distance else False


class SearchRecommendation(models.Model):
    """AI-powered search recommendations based on user history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommended_providers = models.ManyToManyField(
        User, 
        related_name='recommended_for',
        through='RecommendationScore'
    )
    search_query = models.CharField(max_length=255)
    recommendation_type = models.CharField(
        max_length=20,
        choices=[
            ('similar_searches', 'Similar Searches'),
            ('popular_providers', 'Popular Providers'),
            ('nearby_providers', 'Nearby Providers'),
            ('highly_rated', 'Highly Rated'),
            ('recently_active', 'Recently Active'),
        ]
    )
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-score']
        verbose_name = "Search Recommendation"
        verbose_name_plural = "Search Recommendations"

    def __str__(self):
        return f"Recommendation for {self.user.email} - {self.recommendation_type}"


class RecommendationScore(models.Model):
    """Through model for recommendation scores"""
    recommendation = models.ForeignKey(SearchRecommendation, on_delete=models.CASCADE)
    provider = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ['recommendation', 'provider']


class SearchAnalytics(models.Model):
    """Track search performance and popular queries"""
    date = models.DateField()
    query = models.CharField(max_length=255)
    filters = models.JSONField(default=dict)
    search_count = models.PositiveIntegerField(default=0)
    results_count = models.PositiveIntegerField(default=0)
    click_through_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    average_position = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    class Meta:
        unique_together = ['date', 'query']
        ordering = ['-date', '-search_count']
        verbose_name = "Search Analytics"
        verbose_name_plural = "Search Analytics"

    def __str__(self):
        return f"{self.date} - {self.query} ({self.search_count} searches)"
