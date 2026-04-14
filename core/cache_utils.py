from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet, Sum
from functools import wraps
import hashlib
import json
import time
from typing import Any, Optional, Union


class CacheManager:
    """Advanced caching utilities for the freelance platform"""
    
    @staticmethod
    def get_cache_key(prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        # Create a string representation of all arguments
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if hasattr(arg, 'id'):
                key_parts.append(f"{arg.__class__.__name__}_{arg.id}")
            elif isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(hash(str(arg))))
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if hasattr(v, 'id'):
                key_parts.append(f"{k}_{v.__class__.__name__}_{v.id}")
            elif isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}_{v}")
            else:
                key_parts.append(f"{k}_{hash(str(v))}")
        
        # Join and hash to keep key length reasonable
        key_string = "_".join(key_parts)
        
        # Truncate if too long and add hash
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
            key_string = key_string[:192] + "_" + key_hash
        
        return f"pro4me:{key_string}"
    
    @staticmethod
    def cache_result(timeout: int = 300, key_prefix: str = ""):
        """Decorator to cache function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = CacheManager.get_cache_key(
                    key_prefix or f"{func.__module__}.{func.__name__}",
                    *args,
                    **kwargs
                )
                
                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def cache_queryset(timeout: int = 300, key_prefix: str = ""):
        """Decorator to cache QuerySet results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = CacheManager.get_cache_key(
                    key_prefix or f"qs_{func.__module__}.{func.__name__}",
                    *args,
                    **kwargs
                )
                
                # Try to get from cache
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    # Return the list of IDs and let the caller fetch the objects
                    if isinstance(cached_data, list):
                        return cached_data
                
                # Execute function
                queryset = func(*args, **kwargs)
                
                if isinstance(queryset, QuerySet):
                    # Cache only the IDs to avoid large cache entries
                    ids = list(queryset.values_list('id', flat=True))
                    cache.set(cache_key, ids, timeout)
                    return queryset
                else:
                    # Cache the result directly
                    cache.set(cache_key, queryset, timeout)
                    return queryset
            
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_cache_pattern(pattern: str) -> None:
        """Invalidate cache keys matching a pattern"""
        # This is a simplified version - in production, you might want to use
        # Redis pattern matching or maintain a registry of cache keys
        try:
            # Get all keys matching pattern (Redis-specific)
            import redis
            r = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
            keys = r.keys(f"*{pattern}*")
            if keys:
                r.delete(*keys)
        except Exception:
            # Fallback: try to get and delete keys one by one
            pass
    
    @staticmethod
    def cache_user_data(user_id: int, timeout: int = 300) -> dict:
        """Cache frequently accessed user data"""
        cache_key = f"user_data_{user_id}"
        
        # Try to get from cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch user data (this would be implemented in the actual view)
        try:
            from users.models import User
        except ImportError:
            # Fallback for testing
            User = None
        
        try:
            if User is None:
                return None
                
            user = User.objects.select_related('provider_profile').get(id=user_id)
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'bio': getattr(user.provider_profile, 'bio', '') if hasattr(user, 'provider_profile') else '',
                'location': getattr(user.provider_profile, 'location', '') if hasattr(user, 'provider_profile') else '',
                'average_rating': getattr(user.provider_profile, 'average_rating', 0) if hasattr(user, 'provider_profile') else 0,
                'daily_rate': getattr(user.provider_profile, 'daily_rate', None) if hasattr(user, 'provider_profile') else None,
                'is_verified': getattr(user.provider_profile, 'is_verified', False) if hasattr(user, 'provider_profile') else False,
                'is_available_now': getattr(user.provider_profile, 'is_available_now', False) if hasattr(user, 'provider_profile') else False,
            }
            
            # Cache the data
            cache.set(cache_key, user_data, timeout)
            return user_data
            
        except (User.DoesNotExist, AttributeError):
            return None
    
    @staticmethod
    def cache_search_results(query: str, filters: dict, results: list, timeout: int = 600) -> None:
        """Cache search results"""
        cache_key = CacheManager.get_cache_key("search_results", query, **filters)
        cache.set(cache_key, results, timeout)
    
    @staticmethod
    def get_cached_search_results(query: str, filters: dict) -> Optional[list]:
        """Get cached search results"""
        cache_key = CacheManager.get_cache_key("search_results", query, **filters)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_popular_providers(timeout: int = 3600) -> list:
        """Cache popular providers"""
        cache_key = "popular_providers"
        
        # Try to get from cache
        cached_providers = cache.get(cache_key)
        if cached_providers:
            return cached_providers
        
        # Fetch popular providers
        from users.models import User
        
        providers = User.objects.filter(
            user_type='service_provider',
            is_active=True
        ).select_related('provider_profile').filter(
            provider_profile__average_rating__gte=4.0,
            provider_profile__review_count__gte=5
        ).order_by('-provider_profile__average_rating')[:20]
        
        # Cache the results
        provider_data = []
        for provider in providers:
            provider_data.append({
                'id': provider.id,
                'name': provider.get_full_name() or provider.email,
                'rating': provider.provider_profile.average_rating,
                'review_count': provider.provider_profile.review_count,
                'location': provider.provider_profile.location,
                'profile_picture': provider.profile_picture.url if provider.profile_picture else None,
                'daily_rate': provider.provider_profile.daily_rate,
                'is_verified': provider.provider_profile.is_verified,
            })
        
        cache.set(cache_key, provider_data, timeout)
        return provider_data
    
    @staticmethod
    def cache_categories(timeout: int = 7200) -> list:
        """Cache service categories"""
        cache_key = "service_categories"
        
        # Try to get from cache
        cached_categories = cache.get(cache_key)
        if cached_categories:
            return cached_categories
        
        # Fetch categories
        from gigs.models import Category
        
        categories = Category.objects.filter(is_active=True).annotate(
            gig_count=models.Count('gig', filter=models.Q(gig__is_active=True))
        ).order_by('name')
        
        # Cache the results
        category_data = []
        for category in categories:
            category_data.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'description': category.description,
                'icon': category.icon,
                'gig_count': category.gig_count,
            })
        
        cache.set(cache_key, category_data, timeout)
        return category_data
    
    @staticmethod
    def cache_user_notifications(user_id: int, timeout: int = 60) -> list:
        """Cache user notifications"""
        cache_key = f"user_notifications_{user_id}"
        
        # Try to get from cache
        cached_notifications = cache.get(cache_key)
        if cached_notifications:
            return cached_notifications
        
        # Fetch notifications
        from core.models_notifications import Notification
        
        notifications = Notification.objects.filter(
            recipient_id=user_id,
            is_read=False
        ).order_by('-created_at')[:10]
        
        # Cache the results
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'created_at': notification.created_at.isoformat(),
                'action_url': notification.action_url,
                'action_text': notification.action_text,
                'priority': notification.priority,
            })
        
        cache.set(cache_key, notification_data, timeout)
        return notification_data
    
    @staticmethod
    def invalidate_user_cache(user_id: int) -> None:
        """Invalidate all cache entries for a user"""
        patterns = [
            f"user_data_{user_id}",
            f"user_notifications_{user_id}",
        ]
        
        for pattern in patterns:
            cache.delete(pattern)
    
    @staticmethod
    def cache_stats(timeout: int = 300) -> dict:
        """Cache platform statistics"""
        cache_key = "platform_stats"
        
        # Try to get from cache
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        # Calculate stats
        from users.models import User
        from gigs.models import Gig, Category
        from reviews.models import Review
        
        stats = {
            'total_providers': User.objects.filter(user_type='service_provider', is_active=True).count(),
            'total_homeowners': User.objects.filter(user_type='homeowner', is_active=True).count(),
            'total_gigs': Gig.objects.filter(is_active=True).count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'total_reviews': Review.objects.filter(is_active=True).count(),
            'average_rating': Review.objects.filter(is_active=True).aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'] or 0,
        }
        
        # Cache the results
        cache.set(cache_key, stats, timeout)
        return stats


# Cache middleware for automatic caching
class CacheMiddleware:
    """Middleware to automatically cache frequently accessed data"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Cache user data for authenticated users
        if request.user.is_authenticated:
            CacheManager.cache_user_data(request.user.id, timeout=300)
        
        response = self.get_response(request)
        return response


# Cache signals for automatic invalidation
def invalidate_user_cache(sender, instance, **kwargs):
    """Signal handler to invalidate user cache when user data changes"""
    if hasattr(instance, 'id'):
        CacheManager.invalidate_user_cache(instance.id)


def invalidate_search_cache(sender, instance, **kwargs):
    """Signal handler to invalidate search cache when gigs change"""
    CacheManager.invalidate_cache_pattern("search_results")
    CacheManager.invalidate_cache_pattern("popular_providers")


def invalidate_category_cache(sender, instance, **kwargs):
    """Signal handler to invalidate category cache"""
    cache.delete("service_categories")
