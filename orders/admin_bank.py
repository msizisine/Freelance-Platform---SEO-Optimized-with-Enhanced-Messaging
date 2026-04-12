"""
Admin configuration for bank details - only accessible to system admin
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models_bank import BankDetails, EFTPaymentConfirmation

User = get_user_model()


@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    """
    Admin interface for managing bank details - restricted to system admins
    """
    list_display = [
        'bank_name', 
        'account_holder_name', 
        'account_type', 
        'branch_code',
        'is_active',
        'created_at'
    ]
    list_filter = ['bank_name', 'account_type', 'is_active', 'created_at']
    search_fields = ['bank_name', 'account_holder_name', 'account_number']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Bank Information', {
            'fields': (
                'bank_name',
                'branch_code',
                'account_holder_name',
                'account_number',
                'account_type'
            )
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Only superusers can manage bank details"""
        if not request.user.is_superuser:
            return BankDetails.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        """Only superusers can view bank details"""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Only superusers can add bank details"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can change bank details"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete bank details"""
        return request.user.is_superuser


@admin.register(EFTPaymentConfirmation)
class EFTPaymentConfirmationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing EFT payment confirmations
    """
    list_display = [
        'order',
        'user',
        'confirmed_at',
        'is_verified',
        'verified_by',
        'verified_at'
    ]
    list_filter = ['is_verified', 'confirmed_at', 'verified_at']
    search_fields = ['order__order_number', 'user__email', 'notes']
    list_editable = ['is_verified']
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'order',
                'user',
                'confirmed_at',
                'notes'
            )
        }),
        ('Proof of Payment', {
            'fields': ('proof_of_payment',)
        }),
        ('Verification', {
            'fields': (
                'is_verified',
                'verified_by',
                'verified_at'
            )
        })
    )
    
    readonly_fields = ['confirmed_at', 'verified_at']
    
    def save_model(self, request, obj, form, change):
        """Automatically set verified_by when marking as verified"""
        if obj.is_verified and not obj.verified_by:
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        elif not obj.is_verified:
            obj.verified_by = None
            obj.verified_at = None
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Only superusers can manage EFT confirmations"""
        if not request.user.is_superuser:
            return EFTPaymentConfirmation.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        """Only superusers can view EFT confirmations"""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Only superusers can add EFT confirmations"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can change EFT confirmations"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete EFT confirmations"""
        return request.user.is_superuser
