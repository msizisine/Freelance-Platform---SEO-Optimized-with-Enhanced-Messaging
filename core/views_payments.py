"""
Payment Views for Freelance Platform
Handles provider payouts, earnings, transactions, and payment processing
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import csv
from datetime import datetime, timedelta

from .models_payments import (
    ProviderEarnings, ProviderPayout, PaymentTransaction, 
    PaymentMethod, PaymentSettings, Invoice, Refund
)
from .models import User
from gigs.models import Order, Gig

# Try to import payment services (optional modules)
try:
    from .services.payment_service import PaymentProcessingService
except ImportError:
    PaymentProcessingService = None

try:
    from .services.payment_bulk_service import BulkPaymentService
except ImportError:
    BulkPaymentService = None


@login_required
def payout_dashboard(request):
    """Main dashboard for provider payouts and earnings"""
    if request.user.user_type != 'service_provider':
        messages.error(request, "Access denied. Service providers only.")
        return redirect('core:home')
    
    # Get basic stats
    try:
        if PaymentProcessingService:
            available_balance = PaymentProcessingService.get_provider_balance(request.user)
        else:
            available_balance = 0
    except:
        available_balance = 0
    
    # Get recent earnings
    recent_earnings = ProviderEarnings.objects.filter(
        provider=request.user
    ).order_by('-created_at')[:10]
    
    # Get recent payouts
    recent_payouts = ProviderPayout.objects.filter(
        provider=request.user
    ).order_by('-created_at')[:10]
    
    # Get monthly earnings summary
    monthly_earnings = ProviderEarnings.objects.filter(
        provider=request.user,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    context = {
        'available_balance': available_balance,
        'recent_earnings': recent_earnings,
        'recent_payouts': recent_payouts,
        'monthly_earnings': monthly_earnings,
        'pending_payouts': ProviderPayout.objects.filter(
            provider=request.user,
            status='pending'
        ).count(),
        'total_earnings': ProviderEarnings.objects.filter(
            provider=request.user
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'core/payout_dashboard.html', context)


class ProviderEarningsListView(LoginRequiredMixin, ListView):
    """List view for provider earnings"""
    model = ProviderEarnings
    template_name = 'core/provider_earnings_list.html'
    context_object_name = 'earnings'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProviderEarnings.objects.filter(provider=self.request.user)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_earnings'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        return context


class ProviderPayoutCreateView(LoginRequiredMixin, CreateView):
    """Create a new payout request"""
    model = ProviderPayout
    template_name = 'core/provider_payout_form.html'
    fields = ['amount', 'payment_method', 'bank_account', 'notes']
    success_url = reverse_lazy('core:payout_dashboard')
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        form.instance.status = 'pending'
        
        # Check available balance
        try:
            if PaymentProcessingService:
                available_balance = PaymentProcessingService.get_provider_balance(self.request.user)
                if form.instance.amount > available_balance:
                    form.add_error('amount', 'Insufficient balance')
                    return self.form_invalid(form)
        except:
            pass
        
        messages.success(self.request, 'Payout request submitted successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            if PaymentProcessingService:
                context['available_balance'] = PaymentProcessingService.get_provider_balance(self.request.user)
            else:
                context['available_balance'] = 0
        except:
            context['available_balance'] = 0
        return context


class ProviderPayoutListView(LoginRequiredMixin, ListView):
    """List view for provider payouts"""
    model = ProviderPayout
    template_name = 'core/provider_payout_list.html'
    context_object_name = 'payouts'
    paginate_by = 20
    
    def get_queryset(self):
        return ProviderPayout.objects.filter(
            provider=self.request.user
        ).order_by('-created_at')


class ProviderTransactionListView(LoginRequiredMixin, ListView):
    """List view for provider transactions"""
    model = PaymentTransaction
    template_name = 'core/provider_transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            provider=self.request.user
        ).order_by('-created_at')


class AdminPayoutManagementView(LoginRequiredMixin, ListView):
    """Admin view for managing all payouts"""
    model = ProviderPayout
    template_name = 'core/admin_payout_management.html'
    context_object_name = 'payouts'
    paginate_by = 20
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return ProviderPayout.objects.none()
        
        queryset = ProviderPayout.objects.all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')


@login_required
def approve_payout(request, payout_id):
    """Approve a payout request"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    payout = get_object_or_404(ProviderPayout, id=payout_id)
    
    if payout.status != 'pending':
        return JsonResponse({'error': 'Payout already processed'}, status=400)
    
    try:
        # Process payout
        if PaymentProcessingService:
            result = PaymentProcessingService.process_payout(payout)
            if result['success']:
                payout.status = 'approved'
                payout.processed_at = timezone.now()
                payout.save()
                
                # Create transaction record
                PaymentTransaction.objects.create(
                    provider=payout.provider,
                    transaction_type='payout',
                    amount=payout.amount,
                    status='completed',
                    reference=payout.reference,
                    description=f'Payout approved - {payout.reference}'
                )
                
                return JsonResponse({'success': True, 'message': 'Payout approved successfully'})
            else:
                return JsonResponse({'error': result['message']}, status=400)
        else:
            # Fallback processing without payment service
            payout.status = 'approved'
            payout.processed_at = timezone.now()
            payout.save()
            
            PaymentTransaction.objects.create(
                provider=payout.provider,
                transaction_type='payout',
                amount=payout.amount,
                status='completed',
                reference=payout.reference,
                description=f'Payout approved - {payout.reference}'
            )
            
            return JsonResponse({'success': True, 'message': 'Payout approved successfully'})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def complete_payout(request, payout_id):
    """Mark a payout as completed"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    payout = get_object_or_404(ProviderPayout, id=payout_id)
    
    if payout.status != 'approved':
        return JsonResponse({'error': 'Payout must be approved first'}, status=400)
    
    try:
        payout.status = 'completed'
        payout.completed_at = timezone.now()
        payout.save()
        
        return JsonResponse({'success': True, 'message': 'Payout marked as completed'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def reject_payout(request, payout_id):
    """Reject a payout request"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    payout = get_object_or_404(ProviderPayout, id=payout_id)
    
    if payout.status != 'pending':
        return JsonResponse({'error': 'Payout already processed'}, status=400)
    
    try:
        reason = request.POST.get('reason', 'No reason provided')
        payout.status = 'rejected'
        payout.rejected_at = timezone.now()
        payout.rejection_reason = reason
        payout.save()
        
        return JsonResponse({'success': True, 'message': 'Payout rejected'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def generate_monthly_fees(request):
    """Generate monthly fees for all providers"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get all active providers
        providers = User.objects.filter(user_type='service_provider', is_active=True)
        
        generated_count = 0
        for provider in providers:
            # Calculate monthly fee (example: 10% of earnings)
            monthly_earnings = ProviderEarnings.objects.filter(
                provider=provider,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            fee_amount = monthly_earnings * 0.10  # 10% fee
            
            if fee_amount > 0:
                ProviderEarnings.objects.create(
                    provider=provider,
                    amount=-fee_amount,  # Negative amount for fee
                    description=f'Monthly platform fee ({timezone.now().strftime("%B %Y")})',
                    status='pending'
                )
                generated_count += 1
        
        return JsonResponse({
            'success': True, 
            'message': f'Generated {generated_count} monthly fees'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def all_transactions(request):
    """View all transactions (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('core:home')
    
    transactions = PaymentTransaction.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_transactions': transactions.count(),
        'total_amount': transactions.aggregate(Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'core/all_transactions.html', context)


@login_required
def manage_earnings(request):
    """Manage earnings for providers (admin view)"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('core:home')
    
    earnings = ProviderEarnings.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(earnings, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_earnings': earnings.count(),
        'total_amount': earnings.aggregate(Sum('amount'))['total'] or 0,
    }
    
    return render(request, 'core/manage_earnings.html', context)


@login_required
def download_payout_history_csv(request):
    """Download payout history as CSV"""
    if request.user.user_type != 'service_provider':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payout_history.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Amount', 'Status', 'Payment Method', 'Reference'])
    
    payouts = ProviderPayout.objects.filter(provider=request.user).order_by('-created_at')
    
    for payout in payouts:
        writer.writerow([
            payout.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            payout.amount,
            payout.status,
            payout.payment_method,
            payout.reference
        ])
    
    return response


@login_required
def download_payout_requests_csv(request):
    """Download all payout requests as CSV (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payout_requests.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Provider', 'Date', 'Amount', 'Status', 'Payment Method', 'Reference'])
    
    payouts = ProviderPayout.objects.all().order_by('-created_at')
    
    for payout in payouts:
        writer.writerow([
            payout.provider.get_full_name() or payout.provider.email,
            payout.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            payout.amount,
            payout.status,
            payout.payment_method,
            payout.reference
        ])
    
    return response


class BulkPaymentEFTView(LoginRequiredMixin, View):
    """Handle bulk EFT payments for providers"""
    
    def get(self, request):
        if not request.user.is_staff:
            messages.error(request, "Access denied.")
            return redirect('core:home')
        
        # Get pending payouts
        pending_payouts = ProviderPayout.objects.filter(status='pending')
        
        context = {
            'pending_payouts': pending_payouts,
            'total_amount': pending_payouts.aggregate(Sum('amount'))['total'] or 0,
        }
        
        return render(request, 'core/bulk_payment_eft.html', context)
    
    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            payout_ids = request.POST.getlist('payout_ids')
            
            if not payout_ids:
                return JsonResponse({'error': 'No payouts selected'}, status=400)
            
            if BulkPaymentService:
                # Process bulk payments
                result = BulkPaymentService.process_bulk_eft(payout_ids)
                
                if result['success']:
                    # Update payout statuses
                    ProviderPayout.objects.filter(
                        id__in=payout_ids,
                        status='pending'
                    ).update(
                        status='approved',
                        processed_at=timezone.now()
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Processed {len(payout_ids)} bulk payments'
                    })
                else:
                    return JsonResponse({'error': result['message']}, status=400)
            else:
                # Fallback processing without bulk service
                ProviderPayout.objects.filter(
                    id__in=payout_ids,
                    status='pending'
                ).update(
                    status='approved',
                    processed_at=timezone.now()
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Approved {len(payout_ids)} payouts (bulk service unavailable)'
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
