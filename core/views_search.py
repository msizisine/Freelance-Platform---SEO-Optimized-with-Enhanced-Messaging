from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
from urllib.parse import parse_qs, urlencode
import json

from users.models import User
from gigs.models import Gig, Category
from .models_search import SavedSearch, SearchHistory, SearchRecommendation, SearchAnalytics
from .templatetags.admin_custom import add_days


def advanced_search(request):
    """Advanced search with filters for providers"""
    categories = Category.objects.all()
    results = User.objects.filter(
        user_type='service_provider',
        is_active=True
    ).select_related('provider_profile')
    
    # Parse search parameters
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    location = request.GET.get('location', '').strip()
    radius = int(request.GET.get('radius', 25))
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('min_rating')
    sort_by = request.GET.get('sort', 'relevance')
    
    # Availability filters
    available_now = request.GET.get('available_now')
    available_today = request.GET.get('available_today')
    available_this_week = request.GET.get('available_this_week')
    
    # Start with all providers
    queryset = results
    
    # Apply text search
    if query:
        queryset = queryset.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(bio__icontains=query)
        )
    
    # Apply category filter (through gigs)
    if category_id:
        queryset = queryset.filter(
            gig_set__category_id=category_id
        ).distinct()
    
    # Apply location and radius filter
    if location:
        # This would require geocoding - for now, filter by location field
        queryset = queryset.filter(
            Q(provider_profile__location__icontains=location) |
            Q(provider_profile__service_areas__contains=[location])
        )
    
    # Apply price filters
    if min_price:
        queryset = queryset.filter(
            Q(provider_profile__daily_rate__gte=min_price) |
            Q(provider_profile__rate_per_square_meter__gte=min_price)
        )
    if max_price:
        queryset = queryset.filter(
            Q(provider_profile__daily_rate__lte=max_price) |
            Q(provider_profile__rate_per_square_meter__lte=max_price)
        )
    
    # Apply rating filter
    if min_rating:
        queryset = queryset.filter(
            provider_profile__average_rating__gte=min_rating
        )
    
    # Apply availability filters
    if available_now:
        queryset = queryset.filter(provider_profile__is_available_now=True)
    if available_today:
        queryset = queryset.filter(provider_profile__is_available_today=True)
    if available_this_week:
        queryset = queryset.filter(provider_profile__is_available_this_week=True)
    
    # Apply sorting
    if sort_by == 'price_low':
        queryset = queryset.order_by(
            F('provider_profile__daily_rate').asc(nulls_last),
            F('provider_profile__rate_per_square_meter').asc(nulls_last)
        )
    elif sort_by == 'price_high':
        queryset = queryset.order_by(
            F('provider_profile__daily_rate').desc(nulls_last),
            F('provider_profile__rate_per_square_meter').desc(nulls_last)
        )
    elif sort_by == 'rating':
        queryset = queryset.order_by('-provider_profile__average_rating')
    elif sort_by == 'newest':
        queryset = queryset.order_by('-date_joined')
    elif sort_by == 'distance':
        # Would require actual geolocation calculation
        queryset = queryset.order_by('provider_profile__location')
    else:  # relevance
        # Default ordering for relevance
        if query:
            queryset = queryset.order_by('-provider_profile__average_rating')
        else:
            queryset = queryset.order_by('-provider_profile__average_rating')
    
    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Track search history for authenticated users
    if request.user.is_authenticated:
        SearchHistory.objects.create(
            user=request.user,
            query=query or 'all',
            filters={
                'category': category_id,
                'location': location,
                'radius': radius,
                'min_price': min_price,
                'max_price': max_price,
                'min_rating': min_rating,
                'sort': sort_by,
                'available_now': bool(available_now),
                'available_today': bool(available_today),
                'available_this_week': bool(available_this_week)
            },
            results_count=queryset.count()
        )
        
        # Update search analytics
        today = timezone.now().date()
        analytics, created = SearchAnalytics.objects.get_or_create(
            date=today,
            query=query or 'all',
            defaults={'search_count': 1, 'results_count': queryset.count()}
        )
        if not created:
            analytics.search_count += 1
            analytics.save()
    
    # Prepare active filters for display
    active_filters = []
    if query:
        active_filters.append({
            'label': 'Keywords',
            'value': query,
            'remove_url': remove_param('q')
        })
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            active_filters.append({
                'label': 'Category',
                'value': category.name,
                'remove_url': remove_param('category')
            })
        except Category.DoesNotExist:
            pass
    if location:
        active_filters.append({
            'label': 'Location',
            'value': location,
            'remove_url': remove_param('location')
        })
    if radius != 25:
        active_filters.append({
            'label': 'Radius',
            'value': f'{radius} km',
            'remove_url': remove_param('radius')
        })
    if min_price:
        active_filters.append({
            'label': 'Min Price',
            'value': f'R{min_price}',
            'remove_url': remove_param('min_price')
        })
    if max_price:
        active_filters.append({
            'label': 'Max Price',
            'value': f'R{max_price}',
            'remove_url': remove_param('max_price')
        })
    if min_rating:
        active_filters.append({
            'label': 'Min Rating',
            'value': f'{min_rating}+ stars',
            'remove_url': remove_param('min_rating')
        })
    if available_now:
        active_filters.append({
            'label': 'Available Now',
            'value': 'Yes',
            'remove_url': remove_param('available_now')
        })
    if available_today:
        active_filters.append({
            'label': 'Available Today',
            'value': 'Yes',
            'remove_url': remove_param('available_today')
        })
    if available_this_week:
        active_filters.append({
            'label': 'Available This Week',
            'value': 'Yes',
            'remove_url': remove_param('available_this_week')
        })
    
    context = {
        'results': page_obj,
        'categories': categories,
        'active_filters': active_filters,
        'page_obj': page_obj,
    }
    
    return render(request, 'core/advanced_search.html', context)


@login_required
@require_POST
def save_search(request):
    """Save a search query for later use"""
    try:
        data = json.loads(request.body)
        search_name = data.get('name')
        search_description = data.get('description', '')
        email_notifications = data.get('email_notifications', False)
        
        if not search_name:
            return JsonResponse({'error': 'Search name is required'}, status=400)
        
        # Check if user already has a saved search with this name
        if SavedSearch.objects.filter(user=request.user, name=search_name).exists():
            return JsonResponse({'error': 'You already have a saved search with this name'}, status=400)
        
        # Create saved search
        saved_search = SavedSearch.objects.create(
            user=request.user,
            name=search_name,
            description=search_description,
            query=request.META.get('QUERY_STRING', ''),
            url=request.build_absolute_uri(),
            email_notifications=email_notifications
        )
        
        return JsonResponse({
            'success': True,
            'search_id': saved_search.id,
            'message': 'Search saved successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def saved_searches(request):
    """Display user's saved searches"""
    saved_searches = SavedSearch.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-created_at')
    
    return render(request, 'core/saved_searches.html', {
        'saved_searches': saved_searches
    })


@login_required
@require_POST
def delete_saved_search(request, search_id):
    """Delete a saved search"""
    try:
        search = SavedSearch.objects.get(id=search_id, user=request.user)
        search.is_active = False
        search.save()
        return JsonResponse({'success': True})
    except SavedSearch.DoesNotExist:
        return JsonResponse({'error': 'Saved search not found'}, status=404)


@login_required
def search_recommendations(request):
    """Get personalized search recommendations"""
    # Get user's search history
    search_history = SearchHistory.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    recommendations = []
    
    if search_history:
        # Analyze search patterns
        common_queries = search_history.values('query').annotate(
            count=Count('query')
        ).order_by('-count')[:5]
        
        for query_data in common_queries:
            recommendations.append({
                'type': 'similar_searches',
                'query': query_data['query'],
                'count': query_data['count'],
                'url': f"/search/?q={query_data['query']}"
            })
    
    # Add popular providers
    popular_providers = User.objects.filter(
        user_type='service_provider',
        provider_profile__average_rating__gte=4.0,
        provider_profile__review_count__gte=5
    ).order_by('-provider_profile__average_rating')[:5]
    
    for provider in popular_providers:
        recommendations.append({
            'type': 'popular_providers',
            'provider': provider,
            'rating': provider.provider_profile.average_rating,
            'url': f"/users/profile/{provider.id}/"
        })
    
    # Add highly rated nearby providers (if location is available)
    if hasattr(request.user, 'provider_profile') and request.user.provider_profile.location:
        nearby_providers = User.objects.filter(
            user_type='service_provider',
            provider_profile__location__icontains=request.user.provider_profile.location
        ).order_by('-provider_profile__average_rating')[:3]
        
        for provider in nearby_providers:
            recommendations.append({
                'type': 'nearby_providers',
                'provider': provider,
                'rating': provider.provider_profile.average_rating,
                'url': f"/users/profile/{provider.id}/"
            })
    
    return JsonResponse({'recommendations': recommendations})


def remove_param(param):
    """Helper function to remove a parameter from current URL"""
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    
    url = urlparse(request.build_absolute_uri())
    query_params = parse_qs(url.query)
    
    if param in query_params:
        del query_params[param]
    
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((
        url.scheme,
        url.netloc,
        url.path,
        url.params,
        new_query,
        url.fragment
    ))
    
    return new_url


def search_suggestions(request):
    """Provide autocomplete suggestions for search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get suggestions from multiple sources
    suggestions = []
    
    # Provider names
    providers = User.objects.filter(
        user_type='service_provider',
        is_active=True
    ).filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    )[:5]
    
    for provider in providers:
        name = provider.get_full_name() or provider.email
        suggestions.append({
            'type': 'provider',
            'text': name,
            'url': f"/users/profile/{provider.id}/"
        })
    
    # Category suggestions
    categories = Category.objects.filter(name__icontains=query)[:3]
    for category in categories:
        suggestions.append({
            'type': 'category',
            'text': category.name,
            'url': f"/search/?category={category.id}"
        })
    
    # Location suggestions (would need geocoding service)
    locations = User.objects.filter(
        user_type='service_provider',
        provider_profile__location__icontains=query
    ).values_list('provider_profile__location', flat=True).distinct()[:3]
    
    for location in locations:
        if location:
            suggestions.append({
                'type': 'location',
                'text': location,
                'url': f"/search/?location={location}"
            })
    
    return JsonResponse({'suggestions': suggestions})
