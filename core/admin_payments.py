"""
Admin configuration for payment processing models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum
from .models_payments import (
    ProviderEarnings, ProviderPayout, MonthlyServiceFee, PaymentTransaction
)


@admin.register(ProviderEarnings)
class ProviderEarningsAdmin(admin.ModelAdmin):
    """Admin configuration for ProviderEarnings"""
    list_display = ('provider', 'earning_type', 'gross_amount', 'commission_amount', 
                   'net_amount', 'status', 'created_at', 'available_at')
    list_filter = ('status', 'earning_type', 'created_at', 'available_at')
    search_fields = ('provider__email', 'description', 'order__id')
    readonly_fields = ('id', 'commission_amount', 'net_amount', 'created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'order', 'earning_type', 'status')
        }),
        ('Financial Details', {
            'fields': ('gross_amount', 'commission_amount', 'net_amount')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'available_at')
        }),
        ('System Information', {
            'fields': ('id',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider', 'order')
    
    actions = ['mark_as_available', 'mark_as_paid']
    
    def mark_as_available(self, request, queryset):
        """Mark selected earnings as available for withdrawal"""
        from .services.payment_service import PaymentProcessingService
        
        count = 0
        for earning in queryset:
            if earning.status == 'pending':
                PaymentProcessingService.process_earning_completion(earning)
                count += 1
        
        self.message_user(request, f'{count} earnings marked as available for withdrawal.')
    mark_as_available.short_description = 'Mark as available for withdrawal'
    
    def mark_as_paid(self, request, queryset):
        """Mark selected earnings as paid"""
        count = queryset.filter(status='available').update(status='paid')
        self.message_user(request, f'{count} earnings marked as paid.')
    mark_as_paid.short_description = 'Mark as paid'


@admin.register(ProviderPayout)
class ProviderPayoutAdmin(admin.ModelAdmin):
    """Admin configuration for ProviderPayout"""
    list_display = ('provider', 'net_amount', 'payout_method', 'priority', 
                   'status', 'requested_at', 'reference_number', 'action_buttons')
    list_filter = ('status', 'payout_method', 'priority', 'requested_at')
    search_fields = ('provider__email', 'reference_number', 'transaction_id', 'recipient_name')
    readonly_fields = ('id', 'reference_number', 'gross_amount', 'platform_fee', 
                      'processing_fee', 'net_amount', 'requested_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'status', 'priority')
        }),
        ('Financial Details', {
            'fields': ('gross_amount', 'platform_fee', 'processing_fee', 'net_amount')
        }),
        ('Payment Method', {
            'fields': ('payout_method', 'recipient_name', 'recipient_phone', 
                      'recipient_email', 'bank_account', 'bank_name', 'branch_code')
        }),
        ('Reference & Tracking', {
            'fields': ('reference_number', 'transaction_id', 'receipt_url')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'processed_at', 'completed_at')
        }),
        ('Notes', {
            'fields': ('notes', 'admin_notes')
        }),
        ('System Information', {
            'fields': ('id',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider')
    
    def action_buttons(self, obj):
        """Display action buttons for each payout"""
        buttons = []
        
        if obj.status == 'requested':
            approve_url = reverse('core:approve_payout', args=[obj.pk])
            reject_url = reverse('core:reject_payout', args=[obj.pk])
            buttons.append(f'<a href="{approve_url}" class="btn btn-sm btn-success">Approve</a>')
            buttons.append(f'<a href="{reject_url}" class="btn btn-sm btn-danger">Reject</a>')
        elif obj.status == 'approved':
            complete_url = reverse('core:complete_payout', args=[obj.pk])
            buttons.append(f'<a href="{complete_url}" class="btn btn-sm btn-primary">Complete</a>')
        
        return mark_safe(' '.join(buttons))
    action_buttons.short_description = 'Actions'
    
    actions = ['approve_selected', 'reject_selected', 'complete_selected']
    
    def approve_selected(self, request, queryset):
        """Approve selected payouts"""
        from .services.payment_service import PaymentProcessingService
        
        count = 0
        for payout in queryset.filter(status='requested'):
            PaymentProcessingService.approve_payout(payout)
            count += 1
        
        self.message_user(request, f'{count} payouts approved.')
    approve_selected.short_description = 'Approve selected payouts'
    
    def reject_selected(self, request, queryset):
        """Reject selected payouts"""
        count = queryset.filter(status='requested').update(status='cancelled')
        self.message_user(request, f'{count} payouts rejected.')
    reject_selected.short_description = 'Reject selected payouts'
    
    def complete_selected(self, request, queryset):
        """Complete selected payouts"""
        from .services.payment_service import PaymentProcessingService
        
        count = 0
        for payout in queryset.filter(status='approved'):
            PaymentProcessingService.complete_payout(payout)
            count += 1
        
        self.message_user(request, f'{count} payouts completed.')
    complete_selected.short_description = 'Complete selected payouts'


@admin.register(MonthlyServiceFee)
class MonthlyServiceFeeAdmin(admin.ModelAdmin):
    """Admin configuration for MonthlyServiceFee"""
    list_display = ('provider', 'month', 'base_fee', 'additional_fees', 
                   'total_fee', 'status', 'paid_amount', 'paid_at')
    list_filter = ('status', 'month', 'paid_at')
    search_fields = ('provider__email', 'notes')
    readonly_fields = ('id', 'created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'month', 'status')
        }),
        ('Fee Breakdown', {
            'fields': ('base_fee', 'additional_fees', 'total_fee')
        }),
        ('Payment Information', {
            'fields': ('paid_amount', 'paid_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
        ('System Information', {
            'fields': ('id',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider')
    
    actions = ['mark_as_paid', 'mark_as_overdue', 'waive_fees']
    
    def mark_as_paid(self, request, queryset):
        """Mark selected fees as paid"""
        from django.utils import timezone
        count = queryset.filter(status='charged').update(
            status='paid', 
            paid_at=timezone.now()
        )
        self.message_user(request, f'{count} monthly fees marked as paid.')
    mark_as_paid.short_description = 'Mark as paid'
    
    def mark_as_overdue(self, request, queryset):
        """Mark selected fees as overdue"""
        count = queryset.filter(status='pending').update(status='overdue')
        self.message_user(request, f'{count} monthly fees marked as overdue.')
    mark_as_overdue.short_description = 'Mark as overdue'
    
    def waive_fees(self, request, queryset):
        """Waive selected fees"""
        count = queryset.update(status='waived')
        self.message_user(request, f'{count} monthly fees waived.')
    waive_fees.short_description = 'Waive fees'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentTransaction"""
    list_display = ('provider', 'transaction_type', 'amount', 'status', 
                   'description', 'created_at', 'reference_number')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('provider__email', 'description', 'reference_number', 'external_transaction_id')
    readonly_fields = ('id', 'created_at', 'processed_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'transaction_type', 'amount', 'status')
        }),
        ('Related Objects', {
            'fields': ('earning', 'payout', 'monthly_fee')
        }),
        ('Details', {
            'fields': ('description', 'reference_number', 'external_transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        }),
        ('System Information', {
            'fields': ('id',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider', 'earning', 'payout', 'monthly_fee')
    
    def has_add_permission(self, request):
        """Prevent manual creation of transactions"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent manual editing of transactions"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent manual deletion of transactions"""
        return False


# Custom admin site configuration
admin.site.site_header = 'Freelance Platform Administration'
admin.site.site_title = 'Freelance Platform Admin'
admin.site.index_title = 'Welcome to Freelance Platform Administration'
