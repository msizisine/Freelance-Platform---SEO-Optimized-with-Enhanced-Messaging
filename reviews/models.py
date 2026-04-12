from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from orders.models import Order

User = get_user_model()


class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', null=True, blank=True)
    gig = models.ForeignKey('gigs.Gig', on_delete=models.CASCADE)
    
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    
    # Review criteria (optional, for detailed feedback)
    communication = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rating for communication (1-5)"
    )
    quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rating for work quality (1-5)"
    )
    delivery = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True,
        help_text="Rating for delivery time (1-5)"
    )
    
    is_public = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)  # Auto-verified as it's tied to completed order
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['order', 'client']
    
    def __str__(self):
        return f"Review for {self.service_provider.email} - {self.rating} stars"
    
    def get_average_criteria_rating(self):
        criteria_ratings = [self.communication, self.quality, self.delivery]
        valid_ratings = [r for r in criteria_ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None


class ReviewResponse(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='response')
    service_provider = models.ForeignKey(User, on_delete=models.CASCADE)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Response to review for {self.service_provider.email}"


class ReviewHelpful(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.email} found review {'helpful' if self.is_helpful else 'not helpful'}"


class FreelancerStats(models.Model):
    service_provider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    completed_orders = models.PositiveIntegerField(default=0)
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stats for {self.service_provider.email}"
    
    def update_stats(self):
        from django.db.models import Avg, Count, Sum
        
        reviews = self.service_provider.reviews_received.all()
        completed_orders = self.service_provider.service_provider_orders.filter(status='completed')
        
        self.total_reviews = reviews.count()
        self.average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        self.completed_orders = completed_orders.count()
        self.total_earnings = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Update rating breakdowns
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[i] = reviews.filter(rating=i).count()
        
        self.five_star_reviews = rating_counts.get(5, 0)
        self.four_star_reviews = rating_counts.get(4, 0)
        self.three_star_reviews = rating_counts.get(3, 0)
        self.two_star_reviews = rating_counts.get(2, 0)
        self.one_star_reviews = rating_counts.get(1, 0)
        
        self.save()
