"""
User Views for Freelance Platform
Handles user profiles, authentication, and dashboard functionality
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta
from .models import User, Profile, Education, WorkExperience, Certification, Portfolio
from gigs.models import Gig, JobApplication
from orders.models import Order

from reviews.models import Review
from notifications.models import Notification

# Try to import payment services (optional modules)
try:
    from core.services.payment_service import PaymentProcessingService
    from core.models_payments import ProviderEarnings, ProviderPayout, PaymentTransaction
except ImportError:
    PaymentProcessingService = None
    ProviderEarnings = None
    ProviderPayout = None
    PaymentTransaction = None


class ProfileView(LoginRequiredMixin, DetailView):
    """View user profile"""
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        username = self.kwargs.get('username')
        if username:
            return get_object_or_404(User, username=username)
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        
        # Get user's profile
        try:
            profile = profile_user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=profile_user)
        
        context['profile'] = profile
        
        # Get user's gigs if service provider
        if profile_user.user_type == 'service_provider':
            context['gigs'] = Gig.objects.filter(user=profile_user, is_active=True)
            context['completed_orders'] = Order.objects.filter(
                service_provider=profile_user,
                status='completed'
            ).count()
            
            # Get reviews
            context['reviews'] = Review.objects.filter(
                service_provider=profile_user
            ).order_by('-created_at')[:10]
            
            # Calculate average rating
            avg_rating = Review.objects.filter(
                service_provider=profile_user
            ).aggregate(avg_rating=Avg('rating'))['avg_rating']
            context['average_rating'] = avg_rating or 0
        
        # Get user's orders if client
        if profile_user.user_type == 'homeowner':
            context['orders'] = Order.objects.filter(
                client=profile_user
            ).order_by('-created_at')[:10]
        
        # Check if viewing own profile
        context['is_own_profile'] = profile_user == self.request.user
        
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = Profile
    template_name = 'users/profile_update.html'
    fields = [
        'bio', 'location', 'phone', 'website', 'profile_image',
        'skills', 'experience_years', 'hourly_rate', 'daily_rate',
        'rate_per_square_meter', 'service_areas', 'availability_status'
    ]
    success_url = reverse_lazy('users:profile')
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class EducationCreateView(LoginRequiredMixin, CreateView):
    """Add education to profile"""
    model = Education
    template_name = 'users/education_form.html'
    fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Education added successfully!')
        return super().form_valid(form)


class WorkExperienceCreateView(LoginRequiredMixin, CreateView):
    """Add work experience to profile"""
    model = WorkExperience
    template_name = 'users/work_experience_form.html'
    fields = ['company', 'position', 'start_date', 'end_date', 'description']
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Work experience added successfully!')
        return super().form_valid(form)


class CertificationCreateView(LoginRequiredMixin, CreateView):
    """Add certification to profile"""
    model = Certification
    template_name = 'users/certification_form.html'
    fields = ['name', 'issuing_organization', 'issue_date', 'expiry_date', 'credential_id', 'certificate_url']
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Certification added successfully!')
        return super().form_valid(form)


class PortfolioCreateView(LoginRequiredMixin, CreateView):
    """Add portfolio item to profile"""
    model = Portfolio
    template_name = 'users/portfolio_form.html'
    fields = ['title', 'description', 'image', 'project_url', 'technologies_used']
    success_url = reverse_lazy('users:profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Portfolio item added successfully!')
        return super().form_valid(form)


@login_required
def dashboard(request):
    """Main dashboard for users"""
    user = request.user
    
    if user.user_type == 'service_provider':
        return service_provider_dashboard(request)
    elif user.user_type == 'homeowner':
        return homeowner_dashboard(request)
    else:
        return redirect('users:profile_update')


def service_provider_dashboard(request):
    """Dashboard for service providers"""
    user = request.user
    
    # Get basic stats
    active_gigs = Gig.objects.filter(user=user, is_active=True).count()
    total_orders = Order.objects.filter(service_provider=user).count()
    completed_orders = Order.objects.filter(service_provider=user, status='completed').count()
    
    # Get recent orders
    recent_orders = Order.objects.filter(
        service_provider=user
    ).order_by('-created_at')[:5]
    
    # Get job applications
    recent_applications = JobApplication.objects.filter(
        applicant=user
    ).order_by('-applied_at')[:5]
    
    # Get earnings and payment info with error handling
    try:
        if PaymentProcessingService and ProviderEarnings:
            available_balance = PaymentProcessingService.get_provider_balance(user)
            total_earnings = ProviderEarnings.objects.filter(provider=user).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            pending_payouts = ProviderPayout.objects.filter(
                provider=user,
                status='pending'
            ).count()
        else:
            available_balance = 0
            total_earnings = 0
            pending_payouts = 0
    except Exception as e:
        available_balance = 0
        total_earnings = 0
        pending_payouts = 0
    
    # Get notifications
    notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    context = {
        'active_gigs': active_gigs,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'recent_orders': recent_orders,
        'recent_applications': recent_applications,
        'available_balance': available_balance,
        'total_earnings': total_earnings,
        'pending_payouts': pending_payouts,
        'notifications': notifications,
        'unread_notifications_count': notifications.count(),
    }
    
    return render(request, 'users/service_provider_dashboard.html', context)


def homeowner_dashboard(request):
    """Dashboard for homeowners"""
    user = request.user
    
    # Get user's orders
    orders = Order.objects.filter(client=user)
    active_orders = orders.filter(status__in=['pending', 'in_progress']).count()
    completed_orders = orders.filter(status='completed').count()
    
    # Get recent orders
    recent_orders = orders.order_by('-created_at')[:5]
    
    # Get saved gigs (bookmarks)
    # Note: This would require a Bookmark model
    saved_gigs = []
    
    # Get notifications
    notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
        'recent_orders': recent_orders,
        'saved_gigs': saved_gigs,
        'notifications': notifications,
        'unread_notifications_count': notifications.count(),
    }
    
    return render(request, 'users/homeowner_dashboard.html', context)


@login_required
def search_users(request):
    """Search for users (service providers)"""
    query = request.GET.get('q', '')
    user_type = request.GET.get('user_type', 'service_provider')
    
    users = User.objects.filter(
        user_type=user_type,
        is_active=True
    )
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__bio__icontains=query) |
            Q(profile__skills__icontains=query)
        )
    
    # Filter by skills
    skills = request.GET.get('skills')
    if skills:
        skill_list = [skill.strip() for skill in skills.split(',')]
        for skill in skill_list:
            users = users.filter(profile__skills__icontains=skill)
    
    # Filter by location
    location = request.GET.get('location')
    if location:
        users = users.filter(profile__location__icontains=location)
    
    # Filter by availability
    available = request.GET.get('available')
    if available == 'yes':
        users = users.filter(profile__availability_status='available')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'user_type': user_type,
        'total_results': users.count(),
    }
    
    return render(request, 'users/search_results.html', context)


@login_required
@require_POST
def toggle_availability(request):
    """Toggle user availability status"""
    try:
        profile = request.user.profile
        if profile.availability_status == 'available':
            profile.availability_status = 'unavailable'
        else:
            profile.availability_status = 'available'
        profile.save()
        
        return JsonResponse({
            'success': True,
            'status': profile.availability_status
        })
    except Profile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def upload_profile_image(request):
    """Upload profile image"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        profile = request.user.profile
        image = request.FILES.get('profile_image')
        
        if not image:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        # Validate image
        if not image.content_type.startswith('image/'):
            return JsonResponse({'error': 'Invalid file type'}, status=400)
        
        # Update profile image
        profile.profile_image = image
        profile.save()
        
        return JsonResponse({
            'success': True,
            'image_url': profile.profile_image.url if profile.profile_image else None
        })
        
    except Profile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def delete_education(request, education_id):
    """Delete education entry"""
    try:
        education = Education.objects.get(id=education_id, user=request.user)
        education.delete()
        messages.success(request, 'Education deleted successfully!')
        return redirect('users:profile')
    except Education.DoesNotExist:
        messages.error(request, 'Education not found!')
        return redirect('users:profile')


@login_required
def delete_work_experience(request, experience_id):
    """Delete work experience entry"""
    try:
        experience = WorkExperience.objects.get(id=experience_id, user=request.user)
        experience.delete()
        messages.success(request, 'Work experience deleted successfully!')
        return redirect('users:profile')
    except WorkExperience.DoesNotExist:
        messages.error(request, 'Work experience not found!')
        return redirect('users:profile')


@login_required
def delete_certification(request, certification_id):
    """Delete certification entry"""
    try:
        certification = Certification.objects.get(id=certification_id, user=request.user)
        certification.delete()
        messages.success(request, 'Certification deleted successfully!')
        return redirect('users:profile')
    except Certification.DoesNotExist:
        messages.error(request, 'Certification not found!')
        return redirect('users:profile')


@login_required
def delete_portfolio_item(request, portfolio_id):
    """Delete portfolio item"""
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id, user=request.user)
        portfolio.delete()
        messages.success(request, 'Portfolio item deleted successfully!')
        return redirect('users:profile')
    except Portfolio.DoesNotExist:
        messages.error(request, 'Portfolio item not found!')
        return redirect('users:profile')


@login_required
@require_POST
def update_notification_settings(request):
    """Update user notification preferences"""
    try:
        profile = request.user.profile
        
        # Update notification settings
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.sms_notifications = request.POST.get('sms_notifications') == 'on'
        profile.push_notifications = request.POST.get('push_notifications') == 'on'
        
        profile.save()
        
        messages.success(request, 'Notification settings updated successfully!')
        return redirect('users:profile')
        
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found!')
        return redirect('users:profile')
    except Exception as e:
        messages.error(request, f'Error updating settings: {str(e)}')
        return redirect('users:profile')


class UserListView(ListView):
    """List all users (for admin or public directory)"""
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        
        # Filter by user type
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-date_joined')


@login_required
def user_analytics(request):
    """Analytics for user activity (admin view)"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('users:dashboard')
    
    # Get user statistics
    total_users = User.objects.filter(is_active=True).count()
    service_providers = User.objects.filter(user_type='service_provider', is_active=True).count()
    homeowners = User.objects.filter(user_type='homeowner', is_active=True).count()
    
    # Get recent registrations
    recent_users = User.objects.filter(
        is_active=True,
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Get user activity by month
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    
    user_registrations = User.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')[:12]
    
    context = {
        'total_users': total_users,
        'service_providers': service_providers,
        'homeowners': homeowners,
        'recent_users': recent_users,
        'user_registrations': user_registrations,
    }
    
    return render(request, 'users/user_analytics.html', context)
