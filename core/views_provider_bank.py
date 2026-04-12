"""
Views for provider bank account management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models_provider_bank import ProviderBankAccount, PayoutRequest
from .forms_provider_bank import ProviderBankAccountForm, PayoutRequestForm, BankAccountVerificationForm
from .models_payments import ProviderEarnings


class IsServiceProviderMixin(UserPassesTestMixin):
    """Mixin to ensure user is a service provider"""
    
    def test_func(self):
        return self.request.user.user_type == 'service_provider'


class ProviderBankAccountListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    """List provider's bank accounts"""
    model = ProviderBankAccount
    template_name = 'core/provider/bank_account_list.html'
    context_object_name = 'bank_accounts'
    paginate_by = 10
    
    def get_queryset(self):
        return ProviderBankAccount.objects.filter(provider=self.request.user).order_by('-is_default', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_earnings'] = ProviderEarnings.objects.filter(
            provider=self.request.user,
            status='available'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        return context


class ProviderBankAccountCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    """Create a new bank account"""
    model = ProviderBankAccount
    form_class = ProviderBankAccountForm
    template_name = 'core/provider/bank_account_form.html'
    success_url = reverse_lazy('core:bank_account_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['provider'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, 'Bank account added successfully! It will be reviewed by our team.')
        return super().form_valid(form)


class ProviderBankAccountUpdateView(LoginRequiredMixin, IsServiceProviderMixin, UpdateView):
    """Update an existing bank account"""
    model = ProviderBankAccount
    form_class = ProviderBankAccountForm
    template_name = 'core/provider/bank_account_form.html'
    success_url = reverse_lazy('core:bank_account_list')
    
    def get_queryset(self):
        return ProviderBankAccount.objects.filter(provider=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['provider'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Bank account updated successfully!')
        return super().form_valid(form)


class ProviderBankAccountDetailView(LoginRequiredMixin, IsServiceProviderMixin, DetailView):
    """View bank account details"""
    model = ProviderBankAccount
    template_name = 'core/provider/bank_account_detail.html'
    context_object_name = 'bank_account'
    
    def get_queryset(self):
        return ProviderBankAccount.objects.filter(provider=self.request.user)


@login_required
@require_POST
def set_default_bank_account(request, pk):
    """Set a bank account as default"""
    if request.user.user_type != 'service_provider':
        return JsonResponse({'error': 'Only service providers can set default bank accounts'}, status=403)
    
    bank_account = get_object_or_404(ProviderBankAccount, pk=pk, provider=request.user)
    bank_account.set_as_default()
    
    return JsonResponse({'success': True, 'message': 'Default bank account updated'})


@login_required
@require_POST
def delete_bank_account(request, pk):
    """Delete a bank account"""
    if request.user.user_type != 'service_provider':
        return JsonResponse({'error': 'Only service providers can delete bank accounts'}, status=403)
    
    bank_account = get_object_or_404(ProviderBankAccount, pk=pk, provider=request.user)
    
    # Don't allow deletion of default account
    if bank_account.is_default:
        return JsonResponse({'error': 'Cannot delete default bank account'}, status=400)
    
    # Don't allow deletion if there are pending payouts
    if bank_account.payout_requests.filter(status__in=['requested', 'processing', 'approved']).exists():
        return JsonResponse({'error': 'Cannot delete bank account with pending payouts'}, status=400)
    
    bank_account.delete()
    return JsonResponse({'success': True, 'message': 'Bank account deleted'})


class PayoutRequestListView(LoginRequiredMixin, IsServiceProviderMixin, ListView):
    """List provider's payout requests"""
    model = PayoutRequest
    template_name = 'core/provider/payout_request_list.html'
    context_object_name = 'payout_requests'
    paginate_by = 10
    
    def get_queryset(self):
        return PayoutRequest.objects.filter(provider=self.request.user).order_by('-requested_at')


class PayoutRequestCreateView(LoginRequiredMixin, IsServiceProviderMixin, CreateView):
    """Create a new payout request"""
    model = PayoutRequest
    form_class = PayoutRequestForm
    template_name = 'core/provider/payout_request_form.html'
    success_url = reverse_lazy('core:payout_request_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['provider'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, 'Payout request submitted successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_earnings'] = ProviderEarnings.objects.filter(
            provider=self.request.user,
            status='available'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        return context


# Admin views for bank account verification
class AdminBankAccountListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view to list all provider bank accounts"""
    model = ProviderBankAccount
    template_name = 'core/admin/provider_bank_accounts.html'
    context_object_name = 'bank_accounts'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_queryset(self):
        return ProviderBankAccount.objects.select_related('provider').order_by('-is_verified', '-created_at')


class AdminBankAccountDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Admin view to see bank account details"""
    model = ProviderBankAccount
    template_name = 'core/admin/provider_bank_account_detail.html'
    context_object_name = 'bank_account'
    
    def test_func(self):
        return self.request.user.is_superuser


@login_required
@require_POST
def verify_bank_account(request, pk):
    """Admin view to verify a bank account"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Only administrators can verify bank accounts'}, status=403)
    
    bank_account = get_object_or_404(ProviderBankAccount, pk=pk)
    
    if bank_account.is_verified:
        return JsonResponse({'error': 'Bank account is already verified'}, status=400)
    
    bank_account.verify(request.user)
    messages.success(request, f'Bank account for {bank_account.provider.email} has been verified')
    
    return JsonResponse({'success': True, 'message': 'Bank account verified'})


@login_required
@require_POST
def reject_bank_account(request, pk):
    """Admin view to reject a bank account"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Only administrators can reject bank accounts'}, status=403)
    
    bank_account = get_object_or_404(ProviderBankAccount, pk=pk)
    
    if bank_account.is_verified:
        return JsonResponse({'error': 'Cannot reject already verified bank account'}, status=400)
    
    # Mark as inactive instead of deleting
    bank_account.is_active = False
    bank_account.verification_notes = "Rejected by administrator"
    bank_account.save()
    
    messages.success(request, f'Bank account for {bank_account.provider.email} has been rejected')
    
    return JsonResponse({'success': True, 'message': 'Bank account rejected'})
