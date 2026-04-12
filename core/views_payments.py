"""
Views for provider payment processing and management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
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


class ProviderEarningsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List provider's earnings"""
    model = ProviderEarnings
    template_name = 'core/payments/provider_earnings.html'
    context_object_name = 'earnings'
    paginate_by = 20
    
    def test_func(self):
        return is_service_provider(self.request.user)
    
    def get_queryset(self):
        return ProviderEarnings.objects.filter(
            provider=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics
        earnings = self.get_queryset()
        total_earnings = sum(earning.net_amount for earning in earnings)
        total_commissions = sum(earning.commission_amount for earning in earnings)
        available_earnings_amount = sum(earning.net_amount for earning in earnings.filter(status='available'))
        pending_earnings_amount = sum(earning.net_amount for earning in earnings.filter(status='pending'))
        
        # Calculate totals
        total_gross = sum(earning.gross_amount for earning in earnings)
        total_net = total_earnings
        commission_rate = (total_commissions / total_gross * 100) if total_gross > 0 else 0
        
        # Count by status
        pending_count = earnings.filter(status='pending').count()
        available_count = earnings.filter(status='available').count()
        paid_count = earnings.filter(status='paid').count()
        processing_count = earnings.filter(status='processing').count()
        
        # Get available earnings for immediate payment
        available_earnings_list = ProviderEarnings.objects.filter(
            provider=self.request.user,
            status='available'
        ).order_by('-created_at')
        
        context.update({
            'total_earnings': total_earnings,
            'total_commissions': total_commissions,
            'available_earnings': available_earnings_amount,  # Keep as amount for statistics
            'pending_earnings': pending_earnings_amount,     # Keep as amount for statistics
            'total_gross': total_gross,
            'total_net': total_net,
            'commission_rate': commission_rate,
            'pending_count': pending_count,
            'available_count': available_count,
            'paid_count': paid_count,
            'processing_count': processing_count,
            'available_earnings_list': available_earnings_list,  # This is for iteration in template
            'available_balance': PaymentProcessingService.get_provider_balance(self.request.user),
        })
        
        return context


class ProviderPayoutCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new payout request"""
    model = ProviderPayout
    template_name = 'core/payments/payout_request.html'
    fields = []  # Empty fields since we handle form manually
    success_url = reverse_lazy('core:payout_list')
    
    def test_func(self):
        return is_service_provider(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available earnings for selection
        from core.models_payments import ProviderEarnings
        available_earnings = ProviderEarnings.objects.filter(
            provider=self.request.user,
            status='available'
        ).order_by('-created_at')
        
        # Check if a specific earning is requested for immediate payment
        earning_id = self.request.GET.get('earning')
        selected_earning = None
        if earning_id:
            try:
                selected_earning = available_earnings.get(id=earning_id)
                context['selected_earning'] = selected_earning
                context['immediate_payment'] = True
            except ProviderEarnings.DoesNotExist:
                pass
        
        context['available_earnings'] = available_earnings
        context['total_available'] = sum(earning.net_amount for earning in available_earnings)
        context['available_balance'] = PaymentProcessingService.get_provider_balance(self.request.user)
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Get selected earnings
        selected_earnings = request.POST.getlist('selected_earnings')
        if not selected_earnings:
            messages.error(request, "Please select at least one earning to payout.")
            return redirect(request.path)
        
        # Get form data
        payout_method = request.POST.get('payout_method')
        priority = request.POST.get('priority', 'standard')
        bank_account = request.POST.get('bank_account')
        bank_name = request.POST.get('bank_name')
        branch_code = request.POST.get('branch_code')
        
        # Validate required fields
        if not payout_method:
            messages.error(request, "Please select a payment method.")
            return redirect(request.path)
        
        # Validate payment method specific fields
        if payout_method == 'bank_transfer' and not (bank_account and bank_name and branch_code):
            messages.error(request, "Bank account details are required for bank transfers.")
            return redirect(request.path)
        
        try:
            payout = PaymentProcessingService.create_payout_request(
                provider=request.user,
                earnings_ids=selected_earnings,
                payout_method=payout_method,
                priority=priority,
                payment_details={
                    'bank_account': bank_account,
                    'bank_name': bank_name,
                    'branch_code': branch_code,
                }
            )
            
            messages.success(request, f"Payout request of R{payout.net_amount} submitted successfully.")
            return redirect(self.success_url)
            
        except ValueError as e:
            messages.error(request, str(e))
            return redirect(request.path)
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect(request.path)
    


class ProviderPayoutListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List provider's payout requests"""
    model = ProviderPayout
    template_name = 'core/payments/payout_list.html'
    context_object_name = 'payouts'
    paginate_by = 20
    
    def test_func(self):
        return is_service_provider(self.request.user)
    
    def get_queryset(self):
        return ProviderPayout.objects.filter(
            provider=self.request.user
        ).order_by('-requested_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics
        payouts = self.get_queryset()
        pending_payouts = sum(payout.net_amount for payout in payouts.filter(status='requested'))
        processing_payouts = sum(payout.net_amount for payout in payouts.filter(status='processing'))
        completed_payouts = sum(payout.net_amount for payout in payouts.filter(status='completed'))
        total_payouts = sum(payout.net_amount for payout in payouts)
        
        # Get available earnings for immediate payment
        from core.models_payments import ProviderEarnings
        available_earnings = ProviderEarnings.objects.filter(
            provider=self.request.user,
            status='available'
        ).order_by('-created_at')
        
        context.update({
            'pending_payouts': pending_payouts,
            'processing_payouts': processing_payouts,
            'completed_payouts': completed_payouts,
            'total_payouts': total_payouts,
            'available_earnings': available_earnings,
        })
        
        return context


class ProviderTransactionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List provider's transaction history"""
    model = PaymentTransaction
    template_name = 'core/payments/transaction_history.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def test_func(self):
        return is_service_provider(self.request.user)
    
    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            provider=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate statistics
        transactions = self.get_queryset()
        total_earnings = sum(t.amount for t in transactions if t.transaction_type == 'earning' and t.status == 'completed')
        total_payouts = sum(abs(t.amount) for t in transactions if t.transaction_type == 'payout' and t.status == 'completed')
        total_fees = sum(abs(t.amount) for t in transactions if t.transaction_type == 'fee' and t.status == 'completed')
        net_balance = total_earnings - total_payouts - total_fees
        
        # Count by status
        completed_count = transactions.filter(status='completed').count()
        pending_count = transactions.filter(status='pending').count()
        failed_count = transactions.filter(status='failed').count()
        
        # Count by type
        earning_count = transactions.filter(transaction_type='earning').count()
        payout_count = transactions.filter(transaction_type='payout').count()
        fee_count = transactions.filter(transaction_type='fee').count()
        other_count = transactions.count() - earning_count - payout_count - fee_count
        
        context.update({
            'total_earnings': total_earnings,
            'total_payouts': total_payouts,
            'total_fees': total_fees,
            'net_balance': net_balance,
            'completed_count': completed_count,
            'pending_count': pending_count,
            'failed_count': failed_count,
            'earning_count': earning_count,
            'payout_count': payout_count,
            'fee_count': fee_count,
            'other_count': other_count,
        })
        
        return context


class AdminPayoutManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view for managing all payouts"""
    model = ProviderPayout
    template_name = 'core/admin/payout_management.html'
    context_object_name = 'payouts'
    paginate_by = 20
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        return ProviderPayout.objects.all().order_by('-requested_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categorize payouts into 3 types
        context['payout_requests'] = ProviderPayout.objects.filter(
            status='requested'
        ).order_by('-requested_at')
        
        context['payout_history'] = ProviderPayout.objects.filter(
            status__in=['approved', 'completed']
        ).order_by('-processed_at', '-completed_at')
        
        # Get earnings that are available/paid but don't have payout requests yet
        from core.models_payments import ProviderEarnings
        from django.utils import timezone
        
        # Get earnings that are available/paid but don't have payout requests yet
        all_earnings = ProviderEarnings.objects.filter(
            status__in=['available', 'paid']
        ).order_by('-created_at')
        
        # Manual filtering to avoid ORM issues with ManyToMany relationships
        earnings_without_payouts = []
        for earning in all_earnings:
            has_payout = ProviderPayout.objects.filter(earnings=earning).exists()
            if not has_payout:
                earnings_without_payouts.append(earning)
        
        # Separate due earnings (available_at <= now) from pending ones
        now = timezone.now()
        due_earnings = []
        pending_earnings = []
        
        for earning in earnings_without_payouts:
            if earning.available_at and earning.available_at <= now:
                earning.is_due = True
                # Check if provider has verified default bank account
                from core.models_provider_bank import ProviderBankAccount
                bank_account = ProviderBankAccount.objects.filter(
                    provider=earning.provider,
                    is_default=True,
                    is_verified=True
                ).first()
                earning.has_verified_bank = bank_account is not None
                earning.bank_account = bank_account
                due_earnings.append(earning)
            else:
                earning.is_due = False
                pending_earnings.append(earning)
        
        context['payouts_awaiting_processing'] = due_earnings
        context['pending_earnings'] = pending_earnings
        
        # Statistics
        context['payout_requests_count'] = context['payout_requests'].count()
        context['payout_history_count'] = context['payout_history'].count()
        context['payouts_awaiting_processing_count'] = len(due_earnings)
        context['pending_earnings_count'] = len(pending_earnings)
        
        context['total_payout_amount'] = ProviderPayout.objects.filter(
            status='completed'
        ).aggregate(total=Sum('net_amount'))['total'] or 0
        
        context['total_awaiting_amount'] = sum(earning.net_amount for earning in due_earnings)
        context['total_pending_amount'] = sum(earning.net_amount for earning in pending_earnings)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle bulk actions for EFT CSV generation"""
        if 'generate_eft_csv' in request.POST:
            selected_earnings = request.POST.getlist('selected_earnings')
            
            if not selected_earnings:
                messages.error(request, "Please select at least one earning to generate EFT CSV.")
                return redirect('core:admin_payout_management')
            
            # Lazy import to prevent ModuleNotFoundError when Django settings aren't configured
            try:
                from core.services.payment_bulk_service import BulkPaymentService
            except ImportError:
                BulkPaymentService = None
            from core.models_payments import ProviderEarnings
            
            # Get selected earnings
            earnings = ProviderEarnings.objects.filter(
                id__in=selected_earnings,
                status='available'
            ).select_related('provider')
            
            if not earnings:
                messages.error(request, "No valid earnings found for EFT processing.")
                return redirect('core:admin_payout_management')
            
            if not BulkPaymentService:
                messages.error(request, "Bulk payment service not available.")
                return redirect('core:admin_payout_management')
            
            # Generate EFT CSV
            csv_content, stats = BulkPaymentService.generate_eft_csv_from_earnings(earnings)
            
            if csv_content:
                # Create HTTP response with CSV file
                from django.http import HttpResponse
                import datetime
                
                response = HttpResponse(csv_content, content_type='text/csv')
                filename = f"EFT_Payouts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                messages.success(request, f"EFT CSV generated successfully with {stats['processed_count']} payouts totaling R{stats['total_amount']:.2f}")
                return response
            else:
                messages.error(request, "Failed to generate EFT CSV. Please check that selected earnings have complete bank details.")
                return redirect('core:admin_payout_management')
        
        return self.get(request)


@login_required
@user_passes_test(is_service_provider)
def payout_dashboard(request):
    """Provider payout dashboard"""
    context = {
        'available_balance': PaymentProcessingService.get_provider_balance(request.user),
        'total_earnings': ProviderEarnings.objects.filter(
            provider=request.user
        ).aggregate(total=Sum('net_amount'))['total'] or 0,
        'pending_payouts': ProviderPayout.objects.filter(
            provider=request.user,
            status__in=['requested', 'processing', 'approved']
        ).aggregate(total=Sum('net_amount'))['total'] or 0,
        'completed_payouts': ProviderPayout.objects.filter(
            provider=request.user,
            status='completed'
        ).aggregate(total=Sum('net_amount'))['total'] or 0,
        'recent_transactions': PaymentTransaction.objects.filter(
            provider=request.user
        ).order_by('-created_at')[:5],
    }
    return render(request, 'core/payments/payout_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def approve_payout(request, pk):
    """Approve a payout request"""
    payout = get_object_or_404(ProviderPayout, pk=pk)
    
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id', '')
        admin_notes = request.POST.get('admin_notes', '')
        
        PaymentProcessingService.approve_payout(
            payout=payout,
            admin_notes=admin_notes,
            transaction_id=transaction_id
        )
        
        messages.success(request, f"Payout to {payout.provider.email} approved successfully.")
        return redirect('core:admin_payout_management')
    
    return render(request, 'core/admin/approve_payout.html', {'payout': payout})


@login_required
@user_passes_test(is_admin)
def complete_payout(request, pk):
    """Mark a payout as completed"""
    payout = get_object_or_404(ProviderPayout, pk=pk)
    
    if request.method == 'POST':
        receipt_url = request.POST.get('receipt_url', '')
        
        PaymentProcessingService.complete_payout(
            payout=payout,
            receipt_url=receipt_url
        )
        
        messages.success(request, f"Payout to {payout.provider.email} marked as completed.")
        return redirect('core:admin_payout_management')
    
    return render(request, 'core/admin/complete_payout.html', {'payout': payout})


@login_required
@user_passes_test(is_admin)
def reject_payout(request, pk):
    """Reject a payout request"""
    payout = get_object_or_404(ProviderPayout, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        with transaction.atomic():
            payout.status = 'cancelled'
            payout.admin_notes = f"Rejected: {reason}"
            payout.save()
            
            # Return earnings to available status
            payout.earnings.update(status='available')
            
            # Create transaction record
            PaymentTransaction.objects.create(
                provider=payout.provider,
                payout=payout,
                transaction_type='adjustment',
                amount=payout.net_amount,
                description=f"Payout cancelled: {reason}",
                status='completed'
            )
        
        messages.success(request, f"Payout to {payout.provider.email} rejected.")
        return redirect('core:admin_payout_management')
    
    return render(request, 'core/admin/reject_payout.html', {'payout': payout})


@login_required
@user_passes_test(is_admin)
def generate_monthly_fees(request):
    """Generate monthly service fees for all providers"""
    if request.method == 'POST':
        PaymentProcessingService.generate_monthly_fees()
        messages.success(request, "Monthly service fees generated successfully.")
        return redirect('core:admin_payout_management')
    
    context = {
        'current_month': timezone.now().date().replace(day=1)
    }
    return render(request, 'core/admin/generate_fees.html', context)


@login_required
@user_passes_test(is_admin)
def all_transactions(request):
    """View all Platform Fee transactions"""
    # Show all fee transactions (platform fees, commissions, monthly fees, etc.)
    transactions = PaymentTransaction.objects.filter(transaction_type='fee').order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status', '')
    provider_id = request.GET.get('provider', '')
    
    if status:
        transactions = transactions.filter(status=status)
    if provider_id:
        transactions = transactions.filter(provider_id=provider_id)
    
    # Calculate platform fee statistics
    total_platform_fees = sum(t.amount for t in transactions if t.status == 'completed')
    pending_platform_fees = sum(t.amount for t in transactions if t.status == 'pending')
    
    # Get providers for filter dropdown
    providers = User.objects.filter(user_type='service_provider').order_by('email')
    
    context = {
        'transactions': transactions,
        'total_platform_fees': total_platform_fees,
        'pending_platform_fees': pending_platform_fees,
        'providers': providers,
    }
    
    return render(request, 'core/admin/all_transactions.html', context)


@login_required
@user_passes_test(is_admin)
def manage_earnings(request):
    """Manage provider earnings"""
    earnings = ProviderEarnings.objects.all().order_by('-created_at')
    
    # Apply filters
    status = request.GET.get('status', '')
    earning_type = request.GET.get('earning_type', '')
    provider_id = request.GET.get('provider', '')
    
    if status:
        earnings = earnings.filter(status=status)
    if earning_type:
        earnings = earnings.filter(earning_type=earning_type)
    if provider_id:
        earnings = earnings.filter(provider_id=provider_id)
    
    # Calculate statistics
    total_earnings = sum(earning.gross_amount for earning in earnings)
    total_commissions = sum(earning.commission_amount for earning in earnings)
    available_earnings = sum(earning.net_amount for earning in earnings.filter(status='available'))
    
    # Get providers for filter dropdown
    providers = User.objects.filter(user_type='service_provider').order_by('email')
    
    context = {
        'earnings': earnings,
        'total_earnings': total_earnings,
        'total_commissions': total_commissions,
        'available_earnings': available_earnings,
        'providers': providers,
    }
    
    return render(request, 'core/admin/manage_earnings.html', context)


@login_required
@user_passes_test(is_admin)
def download_payout_history_csv(request):
    """Download CSV of completed payout history"""
    from django.http import HttpResponse
    import csv
    import datetime
    
    # Get completed payouts
    payouts = ProviderPayout.objects.filter(
        status='completed'
    ).select_related('provider').order_by('-completed_at')
    
    if not payouts:
        messages.error(request, "No completed payouts found for CSV export.")
        return redirect('core:admin_payout_management')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    filename = f"Payout_History_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # CSV Header
    header = [
        'Payout ID', 'Provider Email', 'Provider Name', 'Net Amount', 'Gross Amount', 
        'Platform Fee', 'Processing Fee', 'Payout Method', 'Priority', 'Reference Number',
        'Requested At', 'Completed At', 'Transaction ID', 'Recipient Name', 'Bank Name'
    ]
    writer.writerow(header)
    
    # CSV Data
    for payout in payouts:
        writer.writerow([
            str(payout.id),
            payout.provider.email,
            f"{payout.provider.first_name} {payout.provider.last_name}".strip() or payout.provider.email,
            f"{payout.net_amount:.2f}",
            f"{payout.gross_amount:.2f}",
            f"{payout.platform_fee:.2f}",
            f"{payout.processing_fee:.2f}",
            payout.get_payout_method_display(),
            payout.get_priority_display(),
            payout.reference_number,
            payout.requested_at.strftime('%Y-%m-%d %H:%M:%S') if payout.requested_at else '',
            payout.completed_at.strftime('%Y-%m-%d %H:%M:%S') if payout.completed_at else '',
            payout.transaction_id or '',
            payout.recipient_name or '',
            payout.bank_name or ''
        ])
    
    return response


@login_required
@user_passes_test(is_admin)
def download_payout_requests_csv(request):
    """Download CSV of pending payout requests"""
    from django.http import HttpResponse
    import csv
    import datetime
    
    # Get pending payout requests
    payouts = ProviderPayout.objects.filter(
        status='requested'
    ).select_related('provider').order_by('-requested_at')
    
    if not payouts:
        messages.error(request, "No payout requests found for CSV export.")
        return redirect('core:admin_payout_management')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    filename = f"Payout_Requests_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # CSV Header
    header = [
        'Payout ID', 'Provider Email', 'Provider Name', 'Net Amount', 'Gross Amount', 
        'Platform Fee', 'Processing Fee', 'Payout Method', 'Priority', 'Reference Number',
        'Requested At', 'Recipient Name', 'Recipient Phone', 'Recipient Email',
        'Bank Account', 'Bank Name', 'Branch Code', 'Notes'
    ]
    writer.writerow(header)
    
    # CSV Data
    for payout in payouts:
        writer.writerow([
            str(payout.id),
            payout.provider.email,
            f"{payout.provider.first_name} {payout.provider.last_name}".strip() or payout.provider.email,
            f"{payout.net_amount:.2f}",
            f"{payout.gross_amount:.2f}",
            f"{payout.platform_fee:.2f}",
            f"{payout.processing_fee:.2f}",
            payout.get_payout_method_display(),
            payout.get_priority_display(),
            payout.reference_number,
            payout.requested_at.strftime('%Y-%m-%d %H:%M:%S') if payout.requested_at else '',
            payout.recipient_name or '',
            payout.recipient_phone or '',
            payout.recipient_email or '',
            payout.bank_account or '',
            payout.bank_name or '',
            payout.branch_code or '',
            payout.notes or ''
        ])
    
    return response
