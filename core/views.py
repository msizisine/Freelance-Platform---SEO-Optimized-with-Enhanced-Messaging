from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from gigs.models import Gig, Category
from .models import User


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_gigs'] = Gig.objects.filter(is_featured=True, is_active=True)[:6]
        context['recent_gigs'] = Gig.objects.filter(is_active=True).order_by('-created_at')[:8]
        context['categories'] = Category.objects.all()
        return context


class SearchView(TemplateView):
    template_name = 'core/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        category = self.request.GET.get('category', '')
        
        gigs = Gig.objects.filter(is_active=True)
        
        if query:
            gigs = gigs.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        if category:
            gigs = gigs.filter(category__name=category)
        
        context['gigs'] = gigs
        context['query'] = query
        context['category'] = category
        return context


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_superuser


def admin_receipts_redirect(request):
    """Redirect old admin/receipts URL to new system/receipts URL"""
    return redirect('core:receipt_transactions')


class AdminServiceProviderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view to list all service providers"""
    model = User
    template_name = 'core/admin/service_provider_list.html'
    context_object_name = 'providers'
    paginate_by = 20
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = User.objects.filter(user_type='service_provider')
        
        # Filter by verification status
        verification_status = self.request.GET.get('verification', '')
        if verification_status == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif verification_status == 'unverified':
            queryset = queryset.filter(is_verified=False)
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(skills__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['verification_filter'] = self.request.GET.get('verification', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['total_providers'] = User.objects.filter(user_type='service_provider').count()
        context['verified_providers'] = User.objects.filter(user_type='service_provider', is_verified=True).count()
        context['unverified_providers'] = User.objects.filter(user_type='service_provider', is_verified=False).count()
        return context


class AdminServiceProviderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Admin view to see service provider details and verify them"""
    model = User
    template_name = 'core/admin/service_provider_detail.html'
    context_object_name = 'provider'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.get_object()
        
        # Get provider's related data
        context['portfolio_items'] = provider.portfolio_items.all()
        context['work_experiences'] = provider.work_experiences.all()
        context['professional_references'] = provider.professional_references.all()
        context['gigs'] = provider.hired_jobs.all()
        context['reviews_given'] = provider.reviews_given.all()
        context['reviews_received'] = provider.reviews_received.all()
        
        return context


@login_required
@user_passes_test(is_admin)
def verify_service_provider(request, pk):
    """Admin action to verify a service provider"""
    provider = get_object_or_404(User, pk=pk, user_type='service_provider')
    
    if request.method == 'POST':
        provider.is_verified = True
        provider.save()
        
        # Send notification to provider
        from notifications.services import NotificationService
        NotificationService.send_notification(
            recipient=provider,
            notification_type='provider_verified',
            title='You are now a Verified Service Provider!',
            notification_message='Your service provider account has been verified by our admin team. You now have a verified badge on your profile.',
            sender=request.user,
            channels=['email', 'sms', 'whatsapp', 'in_app']
        )
        
        messages.success(request, f'Service provider {provider.email} has been verified successfully!')
        
        return redirect('core:admin_provider_detail', pk=pk)
    
    return render(request, 'core/admin/verify_provider.html', {'provider': provider})


@login_required
@user_passes_test(is_admin)
def unverify_service_provider(request, pk):
    """Admin action to unverify a service provider"""
    provider = get_object_or_404(User, pk=pk, user_type='service_provider')
    
    if request.method == 'POST':
        provider.is_verified = False
        provider.save()
        
        # Send notification to provider (will be implemented in communication system)
        messages.warning(request, f'Service provider {provider.email} has been unverified.')
        
        return redirect('core:admin_provider_detail', pk=pk)
    
    return render(request, 'core/admin/unverify_provider.html', {'provider': provider})
