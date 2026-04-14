"""
Views for provider payment processing and management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import date, timedelta
import uuid
import csv

from .models import User
from .models_payments import ProviderEarnings, ProviderPayout, MonthlyServiceFee, PaymentTransaction

# Lazy import to prevent ModuleNotFoundError when Django settings aren't configured
try:
    from .services.payment_service import PaymentProcessingService
except ImportError:
    PaymentProcessingService = None


def is_service_provider(user):
    """Check if user is a service provider"""
    return user.is_authenticated and user.user_type == 'service_provider'


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_superuser


class ProviderEarningsListView(LoginRequiredMixin, ListView):
    """List earnings for the current service provider"""
    model = ProviderEarnings
    template_name = 'core/payments/provider_earnings_list.html'
    context_object_name = 'earnings'
    paginate_by = 20

    def get_queryset(self):
        return ProviderEarnings.objects.filter(provider=self.request.user).order_by('-created_at')


class ProviderPayoutCreateView(LoginRequiredMixin, CreateView):
    """Create a new payout request"""
    model = ProviderPayout
    template_name = 'core/payments/payout_request_form.html'
    fields = ['amount', 'bank_account']
    success_url = reverse_lazy('core:payout_list')

    def form_valid(self, form):
        form.instance.provider = self.request.user
        form.instance.status = 'requested'
        messages.success(self.request, 'Payout request submitted successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add available earnings balance
        available_earnings = ProviderEarnings.objects.filter(
            provider=self.request.user,
            status='available'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        context['available_earnings'] = available_earnings
        return context


class ProviderPayoutListView(LoginRequiredMixin, ListView):
    """List payout requests for the current service provider"""
    model = ProviderPayout
    template_name = 'core/payments/provider_payout_list.html'
    context_object_name = 'payouts'
    paginate_by = 20

    def get_queryset(self):
        return ProviderPayout.objects.filter(provider=self.request.user).order_by('-created_at')


class ProviderTransactionListView(LoginRequiredMixin, ListView):
    """List payment transactions for the current service provider"""
    model = PaymentTransaction
    template_name = 'core/payments/transaction_history.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        return PaymentTransaction.objects.filter(provider=self.request.user).order_by('-created_at')


class AdminPayoutManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view for managing all payout requests"""
    model = ProviderPayout
    template_name = 'core/payments/admin_payout_management.html'
    context_object_name = 'payouts'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = ProviderPayout.objects.all().order_by('-created_at')
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


@login_required
@user_passes_test(is_admin)
def approve_payout(request, pk):
    """Approve a payout request"""
    payout = get_object_or_404(ProviderPayout, pk=pk)
    payout.status = 'approved'
    payout.approved_at = timezone.now()
    payout.approved_by = request.user
    payout.save()
    messages.success(request, 'Payout approved successfully!')
    return redirect('core:admin_payout_management')


@login_required
@user_passes_test(is_admin)
def complete_payout(request, pk):
    """Mark a payout as completed"""
    payout = get_object_or_404(ProviderPayout, pk=pk)
    payout.status = 'completed'
    payout.completed_at = timezone.now()
    payout.completed_by = request.user
    payout.save()
    messages.success(request, 'Payout marked as completed!')
    return redirect('core:admin_payout_management')


@login_required
@user_passes_test(is_admin)
def reject_payout(request, pk):
    """Reject a payout request"""
    payout = get_object_or_404(ProviderPayout, pk=pk)
    payout.status = 'rejected'
    payout.rejected_at = timezone.now()
    payout.rejected_by = request.user
    payout.save()
    messages.success(request, 'Payout rejected!')
    return redirect('core:admin_payout_management')


@login_required
@user_passes_test(is_admin)
def generate_monthly_fees(request):
    """Generate monthly service fees for all providers"""
    if PaymentProcessingService:
        try:
            count = PaymentProcessingService.generate_monthly_fees()
            messages.success(request, f'Generated {count} monthly service fees!')
        except Exception as e:
            messages.error(request, f'Error generating fees: {str(e)}')
    else:
        messages.error(request, 'Payment service not available')
    return redirect('core:system_dashboard')


@login_required
@user_passes_test(is_admin)
def all_transactions(request):
    """Admin view of all transactions"""
    transactions = PaymentTransaction.objects.all().order_by('-created_at')
    return render(request, 'core/payments/admin_all_transactions.html', {
        'transactions': transactions
    })


@login_required
@user_passes_test(is_admin)
def manage_earnings(request):
    """Admin view for managing provider earnings"""
    earnings = ProviderEarnings.objects.all().order_by('-created_at')
    return render(request, 'core/payments/admin_manage_earnings.html', {
        'earnings': earnings
    })


@login_required
def payout_dashboard(request):
    """Dashboard for payout overview"""
    user = request.user
    
    if user.is_superuser:
        # Admin dashboard
        pending_payouts = ProviderPayout.objects.filter(status='requested').count()
        total_payouts = ProviderPayout.objects.count()
        recent_payouts = ProviderPayout.objects.all().order_by('-created_at')[:10]
        
        context = {
            'is_admin': True,
            'pending_payouts': pending_payouts,
            'total_payouts': total_payouts,
            'recent_payouts': recent_payouts,
        }
    else:
        # Provider dashboard
        available_balance = 0
        if PaymentProcessingService:
            try:
                available_balance = PaymentProcessingService.get_provider_balance(user)
            except:
                pass
        
        pending_payouts = ProviderPayout.objects.filter(
            provider=user, 
            status__in=['requested', 'processing', 'approved']
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        recent_transactions = []
        if PaymentProcessingService:
            try:
                recent_transactions = PaymentProcessingService.get_provider_transaction_history(user, limit=5)
            except:
                pass
        
        context = {
            'is_admin': False,
            'available_balance': available_balance,
            'pending_payouts': pending_payouts,
            'recent_transactions': recent_transactions,
        }
    
    return render(request, 'core/payments/payout_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def download_payout_history_csv(request):
    """Download payout history as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payout_history.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Provider', 'Amount', 'Status', 'Created', 'Completed'])
    
    payouts = ProviderPayout.objects.all().order_by('-created_at')
    for payout in payouts:
        writer.writerow([
            payout.provider.email,
            payout.net_amount,
            payout.status,
            payout.created_at,
            payout.completed_at or ''
        ])
    
    return response


@login_required
@user_passes_test(is_admin)
def download_payout_requests_csv(request):
    """Download payout requests as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payout_requests.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Provider', 'Amount', 'Status', 'Requested', 'Approved'])
    
    payouts = ProviderPayout.objects.filter(status='requested').order_by('-created_at')
    for payout in payouts:
        writer.writerow([
            payout.provider.email,
            payout.net_amount,
            payout.status,
            payout.created_at,
            payout.approved_at or ''
        ])
    
    return response
