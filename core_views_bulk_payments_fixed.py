"""
Bulk Payment Views for Freelance Platform
Handles bulk EFT payments, CSV imports, and batch processing
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import csv
import json
from datetime import datetime, timedelta
from io import StringIO

from .models_payments import ProviderPayout, PaymentTransaction
from .models import User

# Try to import bulk payment service (optional module)
try:
    from .services.payment_bulk_service import BulkPaymentService
except ImportError:
    BulkPaymentService = None


class GenerateBulkPaymentView(LoginRequiredMixin, View):
    """Generate bulk payment file for EFT processing"""
    
    def get(self, request):
        if not request.user.is_staff:
            messages.error(request, "Access denied.")
            return redirect('core:home')
        
        # Get pending payouts
        pending_payouts = ProviderPayout.objects.filter(status='pending').select_related('provider')
        
        context = {
            'pending_payouts': pending_payouts,
            'total_amount': pending_payouts.aggregate(Sum('amount'))['total'] or 0,
            'total_count': pending_payouts.count(),
        }
        
        return render(request, 'core/generate_bulk_payment.html', context)
    
    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            payout_ids = request.POST.getlist('payout_ids')
            
            if not payout_ids:
                return JsonResponse({'error': 'No payouts selected'}, status=400)
            
            # Get selected payouts
            payouts = ProviderPayout.objects.filter(
                id__in=payout_ids,
                status='pending'
            ).select_related('provider')
            
            if not payouts.exists():
                return JsonResponse({'error': 'No valid pending payouts found'}, status=400)
            
            # Generate CSV content
            csv_content = self._generate_eft_csv(payouts)
            
            # Create response
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="bulk_payment_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            return response
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _generate_eft_csv(self, payouts):
        """Generate EFT CSV file content"""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Account Number',
            'Account Name',
            'Bank Name',
            'Branch Code',
            'Amount',
            'Reference',
            'Provider ID',
            'Payout ID'
        ])
        
        # Write payout data
        for payout in payouts:
            provider = payout.provider
            bank_account = provider.bank_account if hasattr(provider, 'bank_account') else None
            
            writer.writerow([
                bank_account.account_number if bank_account else '',
                bank_account.account_name if bank_account else provider.get_full_name() or provider.email,
                bank_account.bank_name if bank_account else '',
                bank_account.branch_code if bank_account else '',
                payout.amount,
                payout.reference,
                provider.id,
                payout.id
            ])
        
        return output.getvalue()


class ProcessBulkPaymentView(LoginRequiredMixin, View):
    """Process bulk payment confirmations"""
    
    def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        try:
            action = request.POST.get('action')
            payout_ids = request.POST.getlist('payout_ids')
            
            if not payout_ids:
                return JsonResponse({'error': 'No payouts selected'}, status=400)
            
            if action == 'approve':
                return self._approve_bulk_payments(payout_ids)
            elif action == 'reject':
                return self._reject_bulk_payments(payout_ids)
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _approve_bulk_payments(self, payout_ids):
        """Approve bulk payments"""
        try:
            if BulkPaymentService:
                # Use bulk payment service
                result = BulkPaymentService.process_bulk_approval(payout_ids)
                
                if result['success']:
                    # Update payout statuses
                    ProviderPayout.objects.filter(
                        id__in=payout_ids,
                        status='pending'
                    ).update(
                        status='approved',
                        processed_at=timezone.now()
                    )
                    
                    # Create transaction records
                    payouts = ProviderPayout.objects.filter(id__in=payout_ids)
                    for payout in payouts:
                        PaymentTransaction.objects.create(
                            provider=payout.provider,
                            transaction_type='payout',
                            amount=payout.amount,
                            status='completed',
                            reference=payout.reference,
                            description=f'Bulk payout approved - {payout.reference}'
                        )
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Approved {len(payout_ids)} bulk payments'
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
                
                # Create transaction records
                payouts = ProviderPayout.objects.filter(id__in=payout_ids)
                for payout in payouts:
                    PaymentTransaction.objects.create(
                        provider=payout.provider,
                        transaction_type='payout',
                        amount=payout.amount,
                        status='completed',
                        reference=payout.reference,
                        description=f'Bulk payout approved - {payout.reference}'
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Approved {len(payout_ids)} payouts (bulk service unavailable)'
                })
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _reject_bulk_payments(self, payout_ids):
        """Reject bulk payments"""
        try:
            reason = request.POST.get('reason', 'Bulk rejection')
            
            ProviderPayout.objects.filter(
                id__in=payout_ids,
                status='pending'
            ).update(
                status='rejected',
                rejected_at=timezone.now(),
                rejection_reason=reason
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Rejected {len(payout_ids)} payouts'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class BulkPaymentListView(LoginRequiredMixin, ListView):
    """List view for bulk payment operations"""
    model = ProviderPayout
    template_name = 'core/bulk_payment_list.html'
    context_object_name = 'payouts'
    paginate_by = 50
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return ProviderPayout.objects.none()
        
        queryset = ProviderPayout.objects.all().select_related('provider')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = self.get_queryset()
        context['total_amount'] = queryset.aggregate(Sum('amount'))['total'] or 0
        context['total_count'] = queryset.count()
        context['pending_count'] = queryset.filter(status='pending').count()
        context['approved_count'] = queryset.filter(status='approved').count()
        
        return context


@login_required
def upload_bulk_payment_confirmation(request):
    """Upload bulk payment confirmation file"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        file = request.FILES.get('confirmation_file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        if not file.name.endswith('.csv'):
            return JsonResponse({'error': 'CSV file required'}, status=400)
        
        # Process CSV file
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        
        processed_count = 0
        error_count = 0
        
        for row in reader:
            try:
                payout_id = row.get('Payout ID') or row.get('payout_id')
                if not payout_id:
                    error_count += 1
                    continue
                
                payout = ProviderPayout.objects.get(id=payout_id, status='approved')
                
                # Mark as completed
                payout.status = 'completed'
                payout.completed_at = timezone.now()
                payout.confirmation_reference = row.get('Reference', '')
                payout.save()
                
                processed_count += 1
                
            except ProviderPayout.DoesNotExist:
                error_count += 1
                continue
            except Exception as e:
                error_count += 1
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Processed {processed_count} confirmations, {error_count} errors'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def bulk_payment_summary(request):
    """Get summary of bulk payment operations"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get summary statistics
        summary = {
            'pending_payouts': ProviderPayout.objects.filter(status='pending').count(),
            'pending_amount': ProviderPayout.objects.filter(status='pending').aggregate(Sum('amount'))['total'] or 0,
            'approved_payouts': ProviderPayout.objects.filter(status='approved').count(),
            'approved_amount': ProviderPayout.objects.filter(status='approved').aggregate(Sum('amount'))['total'] or 0,
            'completed_payouts': ProviderPayout.objects.filter(status='completed').count(),
            'completed_amount': ProviderPayout.objects.filter(status='completed').aggregate(Sum('amount'))['total'] or 0,
        }
        
        return JsonResponse({'success': True, 'summary': summary})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_bulk_payment_report(request):
    """Export comprehensive bulk payment report"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Get all payouts
        payouts = ProviderPayout.objects.all().select_related('provider').order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bulk_payment_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Payout ID',
            'Provider Name',
            'Provider Email',
            'Amount',
            'Status',
            'Payment Method',
            'Created Date',
            'Processed Date',
            'Completed Date',
            'Reference',
            'Bank Account',
            'Bank Name',
            'Notes'
        ])
        
        # Write data
        for payout in payouts:
            provider = payout.provider
            bank_account = provider.bank_account if hasattr(provider, 'bank_account') else None
            
            writer.writerow([
                payout.id,
                provider.get_full_name(),
                provider.email,
                payout.amount,
                payout.status,
                payout.payment_method,
                payout.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                payout.processed_at.strftime('%Y-%m-%d %H:%M:%S') if payout.processed_at else '',
                payout.completed_at.strftime('%Y-%m-%d %H:%M:%S') if payout.completed_at else '',
                payout.reference,
                bank_account.account_number if bank_account else '',
                bank_account.bank_name if bank_account else '',
                payout.notes or ''
            ])
        
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
