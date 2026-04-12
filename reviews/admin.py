from django.contrib import admin
from .models import Review, ReviewResponse, ReviewHelpful, FreelancerStats


class ReviewResponseInline(admin.StackedInline):
    model = ReviewResponse
    extra = 0
    readonly_fields = ('created_at',)


class ReviewHelpfulInline(admin.TabularInline):
    model = ReviewHelpful
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'client', 'service_provider', 'rating', 'is_public', 'created_at')
    list_filter = ('rating', 'is_public', 'created_at')
    search_fields = ('client__email', 'service_provider__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ReviewResponseInline, ReviewHelpfulInline]
    
    fieldsets = (
        ('Review Information', {
            'fields': ('order', 'client', 'service_provider', 'gig', 'rating', 'comment')
        }),
        ('Detailed Ratings', {
            'fields': ('communication', 'quality', 'delivery'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_public', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ('review', 'service_provider', 'created_at')
    search_fields = ('review__service_provider__email', 'response')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'is_helpful', 'created_at')
    list_filter = ('is_helpful', 'created_at')
    search_fields = ('review__service_provider__email', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(FreelancerStats)
class FreelancerStatsAdmin(admin.ModelAdmin):
    list_display = (
        'service_provider', 'total_reviews', 'average_rating', 'completed_orders',
        'total_earnings', 'response_rate', 'on_time_delivery_rate'
    )
    list_filter = ('total_reviews', 'average_rating')
    search_fields = ('service_provider__email',)
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        ('Basic Stats', {
            'fields': ('service_provider', 'total_reviews', 'average_rating', 'completed_orders', 'total_earnings')
        }),
        ('Performance Metrics', {
            'fields': ('response_rate', 'on_time_delivery_rate')
        }),
        ('Rating Breakdown', {
            'fields': (
                'five_star_reviews', 'four_star_reviews', 'three_star_reviews',
                'two_star_reviews', 'one_star_reviews'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
