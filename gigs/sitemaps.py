from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Gig, Category
from users.models import User


class GigSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Gig.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('gigs:detail', args=[obj.pk])


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else None

    def location(self, obj):
        return reverse('gigs:category', args=[obj.name])


class StaticSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ['gigs:list', 'gigs:service_providers', 'users:signup', 'account_login']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        from django.utils import timezone
        return timezone.now()


class ProviderSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return User.objects.filter(user_type='service_provider', is_active=True)

    def lastmod(self, obj):
        return obj.last_login if hasattr(obj, 'last_login') else obj.date_joined

    def location(self, obj):
        return reverse('users:profile', args=[obj.pk])
