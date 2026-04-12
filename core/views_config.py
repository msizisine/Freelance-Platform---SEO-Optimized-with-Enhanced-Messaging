"""
Views for system configuration management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum
# Try to import configuration models (optional modules)
try:
    from .models_config import (
        SystemConfiguration, BankAccount, PaymentMethod, 
        PlatformFee, EmailConfiguration
    )
except ImportError as e:
    # Handle missing models gracefully
    print(f"Warning: Could not import some config models: {e}")
    from .models_config import (
        SystemConfiguration, BankAccount, PlatformFee, EmailConfiguration
    )
    PaymentMethod = None
from .models_payments import ProviderEarnings, ProviderPayout, PaymentTransaction
from orders.models import Order

User = get_user_model()


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_superuser


class SystemConfigurationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all system configurations - admin only"""
    model = SystemConfiguration
    template_name = 'core/admin/system_config_list.html'
    context_object_name = 'configurations'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = SystemConfiguration.objects.all()
        config_type = self.request.GET.get('type', '')
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        return queryset.order_by('config_type', 'key')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['config_types'] = SystemConfiguration.CONFIG_TYPES
        context['current_type'] = self.request.GET.get('type', '')
        return context


class SystemConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update system configuration - admin only"""
    model = SystemConfiguration
    template_name = 'core/admin/system_config_form.html'
    fields = ['value', 'description', 'is_active']
    success_url = reverse_lazy('core:system_config_list')
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def form_valid(self, form):
        messages.success(self.request, f'Configuration "{form.instance.key}" updated successfully.')
        return super().form_valid(form)


class BankAccountListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all bank accounts - admin only"""
    model = BankAccount
    template_name = 'core/admin/bank_account_list.html'
    context_object_name = 'accounts'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        return BankAccount.objects.all().order_by('-is_default', 'name')


class PaymentMethodListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all payment methods - admin only"""
    model = PaymentMethod
    template_name = 'core/admin/payment_method_list.html'
    context_object_name = 'methods'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        if PaymentMethod is None:
            return []
        return PaymentMethod.objects.all().order_by('sort_order', 'name')


class PlatformFeeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all platform fees - admin only"""
    model = PlatformFee
    template_name = 'core/admin/platform_fee_list.html'
    context_object_name = 'fees'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        return PlatformFee.objects.all().order_by('fee_type')


class EmailConfigurationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all email configurations - admin only"""
    model = EmailConfiguration
    template_name = 'core/admin/email_config_list.html'
    context_object_name = 'configs'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        return EmailConfiguration.objects.all().order_by('-is_active', 'config_type')


@login_required
@user_passes_test(is_admin)
def system_dashboard(request):
    """System configuration dashboard - admin only"""
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect('core:home')
    
    # Get statistics for dashboard
    total_configs = SystemConfiguration.objects.count()
    active_configs = SystemConfiguration.objects.filter(is_active=True).count()
    total_bank_accounts = BankAccount.objects.count()
    active_bank_accounts = BankAccount.objects.filter(is_active=True).count()
    
    # Handle PaymentMethod being None
    if PaymentMethod is not None:
        total_payment_methods = PaymentMethod.objects.count()
        active_payment_methods = PaymentMethod.objects.filter(is_active=True).count()
    else:
        total_payment_methods = 0
        active_payment_methods = 0
    
    total_platform_fees = PlatformFee.objects.count()
    active_platform_fees = PlatformFee.objects.filter(is_active=True).count()
    email_configs = EmailConfiguration.objects.count()
    
    # Provider statistics
    total_providers = User.objects.filter(user_type='service_provider').count()
    verified_providers = User.objects.filter(user_type='service_provider', is_verified=True).count()
    pending_verification = total_providers - verified_providers
    
    # Homeowner statistics
    total_homeowners = User.objects.filter(user_type='homeowner').count()
    
    # Payment statistics
    total_provider_earnings = ProviderEarnings.objects.aggregate(
        total=Sum('net_amount')
    )['total'] or 0
    total_provider_payouts = ProviderPayout.objects.filter(
        status='completed'
    ).aggregate(total=Sum('net_amount'))['total'] or 0
    
    total_homeowner_payments = Order.objects.filter(
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    pending_homeowner_payments = Order.objects.filter(
        status__in=['pending', 'in_progress']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_transactions = PaymentTransaction.objects.count()
    completed_transactions = PaymentTransaction.objects.filter(status='completed').count()
    
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='completed').count()
    pending_orders = Order.objects.filter(status__in=['pending', 'in_progress']).count()
    
    context = {
        'total_configs': total_configs,
        'active_configs': active_configs,
        'total_bank_accounts': total_bank_accounts,
        'active_bank_accounts': active_bank_accounts,
        'total_payment_methods': total_payment_methods,
        'active_payment_methods': active_payment_methods,
        'total_platform_fees': total_platform_fees,
        'active_platform_fees': active_platform_fees,
        'email_configs': email_configs,
        'total_providers': total_providers,
        'verified_providers': verified_providers,
        'pending_verification': pending_verification,
        'total_homeowners': total_homeowners,
        'total_provider_earnings': total_provider_earnings,
        'total_provider_payouts': total_provider_payouts,
        'total_homeowner_payments': total_homeowner_payments,
        'pending_homeowner_payments': pending_homeowner_payments,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
    }
    return render(request, 'core/admin/system_dashboard.html', context)
