from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.db.models import Avg, Count, Sum, Q
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .forms import ServiceProviderProfileForm, HomeownerProfileForm, PortfolioForm, WorkExperienceForm, ProfessionalReferenceForm
from core.models import Portfolio, WorkExperience, ProfessionalReference, PortfolioImage
from gigs.models import Gig
from reviews.models import Review
from orders.models import Order

@login_required
def dashboard(request):
    """User dashboard view with payment functionality for service providers"""
    user = request.user
    context = {
        'user': user,
        'recent_orders': Order.objects.filter(homeowner=user).order_by('-created_at')[:5],
        'active_orders': Order.objects.filter(homeowner=user, status='in_progress').count(),
        'completed_orders': Order.objects.filter(homeowner=user, status='completed').count(),
        'pending_orders': Order.objects.filter(homeowner=user, status='pending').count(),
    }
    
    # Add payment functionality for service providers
    if user.user_type == 'service_provider':
        try:
            from core.services.payment_service import PaymentProcessingService
            from core.models_payments import ProviderEarnings, ProviderPayout, PaymentTransaction
            
            # Get payment statistics
            available_balance = PaymentProcessingService.get_provider_balance(user)
        except ImportError:
            # Handle case where payment service is not available
            available_balance = 0
            PaymentProcessingService = None
            ProviderEarnings = None
            ProviderPayout = None
            PaymentTransaction = None
        if PaymentProcessingService:
            recent_transactions = PaymentProcessingService.get_provider_transaction_history(user, limit=5)
        else:
            recent_transactions = []
        
        if ProviderPayout:
            pending_payouts = ProviderPayout.objects.filter(
                provider=user, 
                status__in=['requested', 'processing', 'approved']
            ).aggregate(total=Sum('net_amount'))['total'] or 0
        else:
            pending_payouts = 0
        
        # Get available earnings for immediate payment request
        if ProviderEarnings:
            available_earnings = ProviderEarnings.objects.filter(
                provider=user,
                status='available'
            ).order_by('-created_at')
        else:
            available_earnings = []
        
        if ProviderEarnings:
            total_earnings = ProviderEarnings.objects.filter(provider=user).aggregate(
                total=Sum('net_amount')
            )['total'] or 0
        else:
            total_earnings = 0
            
        if ProviderPayout:
            completed_payouts = ProviderPayout.objects.filter(
                provider=user, 
                status='completed'
            ).aggregate(total=Sum('net_amount'))['total'] or 0
        else:
            completed_payouts = 0
        
        context.update({
            'available_balance': available_balance,
            'recent_transactions': recent_transactions,
            'pending_payouts': pending_payouts,
            'available_earnings': available_earnings,
            'total_earnings': total_earnings,
            'completed_payouts': completed_payouts,
        })
    
    return render(request, 'users/dashboard.html', context)
