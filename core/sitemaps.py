from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps import GenericSitemap
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from users.models import User
from gigs.models import Gig, Category
from reviews.models import Review
from core.models_search import ProviderProfile


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'core:home',
            'core:search',
            'gigs:list',
            'gigs:service_providers',
            'users:signup',
            'account_login',
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        # Return recent modification date for static pages
        return timezone.now() - timedelta(days=7)


class ProviderSitemap(Sitemap):
    """Sitemap for service provider profiles"""
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return User.objects.filter(
            user_type='service_provider',
            is_active=True
        ).select_related('provider_profile')

    def location(self, obj):
        return f'/users/profile/{obj.id}/'

    def lastmod(self, obj):
        # Use profile update time or user last login
        if hasattr(obj, 'provider_profile') and obj.provider_profile:
            return obj.provider_profile.updated_at
        return obj.last_login or obj.date_joined

    def priority(self, obj):
        # Higher priority for verified and highly-rated providers
        base_priority = 0.8
        if hasattr(obj, 'provider_profile') and obj.provider_profile:
            if obj.provider_profile.is_verified:
                base_priority += 0.1
            if obj.provider_profile.average_rating >= 4.0:
                base_priority += 0.1
        return min(base_priority, 1.0)


class GigSitemap(Sitemap):
    """Sitemap for gigs/jobs"""
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Gig.objects.filter(
            is_active=True
        ).select_related('category', 'user')

    def location(self, obj):
        return f'/gigs/{obj.id}/'

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        # Higher priority for recently updated gigs
        days_old = (timezone.now() - obj.updated_at).days
        if days_old <= 7:
            return 0.9
        elif days_old <= 30:
            return 0.8
        else:
            return 0.7


class CategorySitemap(Sitemap):
    """Sitemap for service categories"""
    changefreq = 'monthly'
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return f'/gigs/category/{obj.slug}/'

    def lastmod(self, obj):
        return obj.updated_at


class ReviewSitemap(Sitemap):
    """Sitemap for reviews (helps with local SEO)"""
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Review.objects.filter(
            is_active=True
        ).select_related('service_provider', 'homeowner')

    def location(self, obj):
        return f'/reviews/{obj.id}/'

    def lastmod(self, obj):
        return obj.created_at


class BlogSitemap(Sitemap):
    """Sitemap for blog posts (if you add a blog)"""
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        # This would be for a blog app if you add one
        return []

    def location(self, obj):
        return f'/blog/{obj.slug}/'

    def lastmod(self, obj):
        return obj.updated_at


class LocationSitemap(Sitemap):
    """Sitemap for location-based pages"""
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        # Get unique locations from provider profiles
        locations = ProviderProfile.objects.filter(
            location__isnull=False
        ).values_list('location', flat=True).distinct()
        
        # Add major South African cities
        major_cities = [
            'johannesburg', 'cape-town', 'durban', 'pretoria', 
            'port-elizabeth', 'bloemfontein', 'east-london',
            'pietermaritzburg', 'nelson-mandela-bay', 'polokwane'
        ]
        
        return list(locations) + major_cities

    def location(self, obj):
        return f'/search/?location={obj}'

    def lastmod(self, obj):
        return timezone.now() - timedelta(days=30)


class ServiceAreaSitemap(Sitemap):
    """Sitemap for different service areas"""
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        # Common services in South Africa
        services = [
            'plumbing', 'electrical', 'painting', 'carpentry',
            'roofing', 'landscaping', 'cleaning', 'security',
            'air-conditioning', 'solar-installation', 'pool-maintenance',
            'pest-control', 'waste-removal', 'moving-services',
            'home-renovation', 'kitchen-installation', 'bathroom-renovation'
        ]
        return services

    def location(self, obj):
        return f'/search/?q={obj}'

    def lastmod(self, obj):
        return timezone.now() - timedelta(days=15)


# Sitemap configuration
SITEMAPS = {
    'static': StaticViewSitemap,
    'providers': ProviderSitemap,
    'gigs': GigSitemap,
    'categories': CategorySitemap,
    'reviews': ReviewSitemap,
    'locations': LocationSitemap,
    'services': ServiceAreaSitemap,
}
