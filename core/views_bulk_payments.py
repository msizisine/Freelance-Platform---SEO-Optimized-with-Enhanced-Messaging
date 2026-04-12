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
from core.models import User

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
