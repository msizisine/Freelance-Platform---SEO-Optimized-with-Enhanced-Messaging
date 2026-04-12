"""
Bulk Payment Processing Views
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.db.models import Sum

from core.models_payments import ProviderPayout
from core.models_bulk_payments import PaymentBatch, BulkPaymentSettings
# Lazy import to prevent ModuleNotFoundError when Django settings aren't configured
try:
    from core.services.payment_bulk_service import BulkPaymentService
except ImportError:
    BulkPaymentService = None
from core.views import is_admin


class BulkPaymentDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Dashboard for bulk payment processing"""
    model = PaymentBatch
    template_name = 'core/admin/bulk_payment_dashboard.html'
    context_object_name = 'batches'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        return PaymentBatch.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get approved payouts ready for processing
        approved_payouts = ProviderPayout.objects.filter(status='approved')
        
        # Statistics
        context['approved_payouts_count'] = approved_payouts.count()
        context['approved_total_amount'] = approved_payouts.aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        
        # Payout breakdown by method
        context['ewallet_payouts'] = approved_payouts.filter(
            payout_method__in=['ewallet', 'cash_send', 'payshap'],
            recipient_phone__isnull=False
        ).count()
        
        context['eft_payouts'] = approved_payouts.filter(
            payout_method='bank_transfer',
            bank_account__isnull=False
        ).count()
        
        # Recent batches
        context['recent_batches'] = self.get_queryset()[:5]
        
        return context


class GenerateBulkPaymentView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Generate bulk payment CSV files"""
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def post(self, request):
        payment_type = request.POST.get('payment_type', 'mixed')
        selected_payouts = request.POST.getlist('selected_payouts')
        
        if not selected_payouts:
            messages.error(request, "Please select at least one payout to process.")
            return redirect('core:bulk_payment_dashboard')
        
        # Get selected payouts
        payouts = ProviderPayout.objects.filter(id__in=selected_payouts)
        
        if not BulkPaymentService:
            messages.error(request, "Bulk payment service not available.")
            return redirect('core:bulk_payment_dashboard')
            
        try:
            if payment_type == 'ewallet':
                csv_content, stats = BulkPaymentService.generate_ewallet_csv(payouts)
                if csv_content:
                    # Create batch record
                    batch = BulkPaymentService.create_payment_batch(
                        'ewallet', selected_payouts, csv_content
                    )
                    
                    # Mark payouts as processing
                    BulkPaymentService.mark_payouts_as_processing(selected_payouts)
                    
                    messages.success(request, f"Generated eWallet CSV with {stats['processed_count']} payments totaling R{stats['total_amount']:.2f}")
                    return self.download_csv(csv_content, f"ewallet_batch_{batch.id}.csv")
                else:
                    messages.error(request, "No eWallet-compatible payouts found (missing phone numbers).")
                    
            elif payment_type == 'eft':
                csv_content, stats = BulkPaymentService.generate_eft_csv(payouts)
                if csv_content:
                    # Create batch record
                    batch = BulkPaymentService.create_payment_batch(
                        'eft', selected_payouts, csv_content
                    )
                    
                    # Mark payouts as processing
                    BulkPaymentService.mark_payouts_as_processing(selected_payouts)
                    
                    messages.success(request, f"Generated EFT CSV with {stats['processed_count']} payments totaling R{stats['total_amount']:.2f}")
                    return self.download_csv(csv_content, f"eft_batch_{batch.id}.csv")
                else:
                    messages.error(request, "No EFT-compatible payouts found (missing bank details).")
                    
            else:  # mixed
                results = BulkPaymentService.generate_mixed_csv(payouts)
                
                if not results:
                    messages.error(request, "No compatible payouts found for processing.")
                    return redirect('core:bulk_payment_dashboard')
                
                # Create separate batches for each type
                batch_ids = []
                for payment_type, data in results.items():
                    batch = BulkPaymentService.create_payment_batch(
                        payment_type, selected_payouts, data['csv_content']
                    )
                    batch_ids.append(batch.id)
                    
                    stats = data['stats']
                    messages.success(request, 
                        f"Generated {payment_type.upper()} CSV with {stats['processed_count']} payments "
                        f"totaling R{stats['total_amount']:.2f}"
                    )
                
                # Mark payouts as processing
                BulkPaymentService.mark_payouts_as_processing(selected_payouts)
                
                # Return the first CSV for download
                first_type = list(results.keys())[0]
                first_data = results[first_type]
                return self.download_csv(first_data['csv_content'], f"{first_type}_batch_{batch_ids[0]}.csv")
                
        except Exception as e:
            messages.error(request, f"Error generating CSV: {str(e)}")
        
        return redirect('core:bulk_payment_dashboard')
    
    def download_csv(self, csv_content, filename):
        """Download CSV file"""
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PayoutSelectionView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for selecting payouts for bulk processing"""
    model = ProviderPayout
    template_name = 'core/admin/payout_selection.html'
    context_object_name = 'payouts'
    paginate_by = 50
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = ProviderPayout.objects.filter(status='approved').select_related('provider')
        
        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payout_method=payment_method)
        
        # Filter by provider
        provider_id = self.request.GET.get('provider')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['payment_methods'] = ProviderPayout.PAYOUT_METHODS
        context['providers'] = User.objects.filter(user_type='service_provider').order_by('email')
        
        # Current filters
        context['current_method'] = self.request.GET.get('payment_method', '')
        context['current_provider'] = self.request.GET.get('provider', '')
        
        return context


class BatchDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detail view for payment batch"""
    model = PaymentBatch
    template_name = 'core/admin/batch_detail.html'
    context_object_name = 'batch'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.get_object()
        
        # Get associated payouts
        context['payouts'] = batch.payouts.all().select_related('provider')
        
        # Statistics
        context['total_amount'] = batch.payouts.aggregate(
            total=Sum('net_amount')
        )['total'] or 0
        
        return context


class UpdateBatchStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Update batch status"""
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def post(self, request, pk):
        batch = get_object_or_404(PaymentBatch, pk=pk)
        action = request.POST.get('action')
        
        if action == 'upload':
            bank_reference = request.POST.get('bank_reference', '')
            batch.mark_as_uploaded(bank_reference)
            messages.success(request, f"Batch {batch.id} marked as uploaded to bank.")
            
        elif action == 'complete':
            batch.mark_as_completed()
            messages.success(request, f"Batch {batch.id} marked as completed.")
            
        elif action == 'fail':
            error_message = request.POST.get('error_message', '')
            batch.mark_as_failed(error_message)
            messages.error(request, f"Batch {batch.id} marked as failed.")
        
        return redirect('core:batch_detail', pk=batch.id)


class DownloadBatchCSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Download CSV for existing batch"""
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get(self, request, pk):
        batch = get_object_or_404(PaymentBatch, pk=pk)
        
        if not batch.csv_content:
            messages.error(request, "No CSV content available for this batch.")
            return redirect('core:batch_detail', pk=batch.id)
        
        response = HttpResponse(batch.csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{batch.filename}"'
        return response
