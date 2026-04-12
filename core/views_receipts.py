"""
Views for payment receipt and transaction management
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q
from django.utils import timezone
from django.db.models.functions import TruncDate, TruncMonth
from .models_receipts import PaymentReceipt, ReceiptTransaction
from orders.models import Order


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_superuser


@login_required
@user_passes_test(is_admin)
def receipt_transaction_list(request):
    """View all payment receipts and transactions for administrators"""
    
    # Get filter parameters
    payment_method = request.GET.get('payment_method', '')
    payment_status = request.GET.get('payment_status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    receipts = PaymentReceipt.objects.all()
    
    # Apply filters
    if payment_method:
        receipts = receipts.filter(payment_method=payment_method)
    if payment_status:
        receipts = receipts.filter(payment_status=payment_status)
    if date_from:
        receipts = receipts.filter(payment_date__gte=date_from)
    if date_to:
        receipts = receipts.filter(payment_date__lte=date_to)
    
    # Order by most recent
    receipts = receipts.order_by('-created_at')
    
    # Calculate statistics
    total_receipts = receipts.count()
    completed_receipts = receipts.filter(payment_status='completed').count()
    total_amount = receipts.aggregate(total=Sum('amount'))['total'] or 0
    completed_amount = receipts.filter(payment_status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
    # Payment method breakdown
    eft_count = receipts.filter(payment_method='eft').count()
    eft_amount = receipts.filter(payment_method='eft').aggregate(total=Sum('amount'))['total'] or 0
    ozow_count = receipts.filter(payment_method='ozow').count()
    ozow_amount = receipts.filter(payment_method='ozow').aggregate(total=Sum('amount'))['total'] or 0
    cash_count = receipts.filter(payment_method='cash').count()
    cash_amount = receipts.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or 0
    other_count = receipts.filter(payment_method='other').count()
    other_amount = receipts.filter(payment_method='other').aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent transactions
    recent_receipts = receipts[:10]
    
    # Monthly statistics (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_stats = []
    
    for i in range(6):
        month_start = (timezone.now() - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_receipts = receipts.filter(payment_date__range=[month_start, month_end])
        month_total = month_receipts.aggregate(total=Sum('amount'))['total'] or 0
        month_count = month_receipts.count()
        
        monthly_stats.append({
            'month': month_start.strftime('%B %Y'),
            'total': month_total,
            'count': month_count
        })
    
    context = {
        'receipts': receipts,
        'recent_receipts': recent_receipts,
        'total_receipts': total_receipts,
        'completed_receipts': completed_receipts,
        'total_amount': total_amount,
        'completed_amount': completed_amount,
        'pending_amount': total_amount - completed_amount,
        # Payment method stats
        'eft_count': eft_count,
        'eft_amount': eft_amount,
        'ozow_count': ozow_count,
        'ozow_amount': ozow_amount,
        'cash_count': cash_count,
        'cash_amount': cash_amount,
        'other_count': other_count,
        'other_amount': other_amount,
        'monthly_stats': monthly_stats,
        # Filter values
        'payment_method': payment_method,
        'payment_status': payment_status,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'core/admin/receipt_transactions.html', context)


@login_required
@user_passes_test(is_admin)
def payment_receipt_dashboard(request):
    """Dashboard view for payment receipts"""
    
    # Get recent receipts
    recent_receipts = PaymentReceipt.objects.order_by('-created_at')[:10]
    
    # Calculate overall statistics
    total_receipts = PaymentReceipt.objects.count()
    completed_receipts = PaymentReceipt.objects.filter(payment_status='completed').count()
    pending_receipts = PaymentReceipt.objects.filter(payment_status='pending').count()
    failed_receipts = PaymentReceipt.objects.filter(payment_status='failed').count()
    
    # Total amounts
    total_amount = PaymentReceipt.objects.aggregate(total=Sum('amount'))['total'] or 0
    completed_amount = PaymentReceipt.objects.filter(payment_status='completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = PaymentReceipt.objects.filter(payment_status='pending').aggregate(total=Sum('amount'))['total'] or 0
    
    # Today's receipts
    today = timezone.now().date()
    today_receipts = PaymentReceipt.objects.filter(payment_date=today)
    today_count = today_receipts.count()
    today_amount = today_receipts.aggregate(total=Sum('amount'))['total'] or 0
    
    # This week's receipts
    week_start = today - timezone.timedelta(days=today.weekday())
    week_receipts = PaymentReceipt.objects.filter(payment_date__gte=week_start)
    week_count = week_receipts.count()
    week_amount = week_receipts.aggregate(total=Sum('amount'))['total'] or 0
    
    # This month's receipts
    month_start = today.replace(day=1)
    month_receipts = PaymentReceipt.objects.filter(payment_date__gte=month_start)
    month_count = month_receipts.count()
    month_amount = month_receipts.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'recent_receipts': recent_receipts,
        'total_receipts': total_receipts,
        'completed_receipts': completed_receipts,
        'pending_receipts': pending_receipts,
        'failed_receipts': failed_receipts,
        'total_amount': total_amount,
        'completed_amount': completed_amount,
        'pending_amount': pending_amount,
        'today_count': today_count,
        'today_amount': today_amount,
        'week_count': week_count,
        'week_amount': week_amount,
        'month_count': month_count,
        'month_amount': month_amount,
    }
    
    return render(request, 'core/admin/receipt_dashboard.html', context)
