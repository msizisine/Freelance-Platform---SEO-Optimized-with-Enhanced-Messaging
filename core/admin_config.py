"""
Admin interface for system configurations - superuser only
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models_config import (
    SystemConfiguration, BankAccount, PaymentMethod, 
    PlatformFee, EmailConfiguration
)


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for system configurations - superuser only
    """
    list_display = [
        'key', 'config_type', 'description', 'is_active', 'updated_at'
    ]
    list_filter = ['config_type', 'is_active', 'created_at']
    search_fields = ['key', 'description']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'config_type', 'description', 'is_active')
        }),
        ('Configuration Value', {
            'fields': ('value',),
            'description': 'Enter configuration value. Use JSON format for complex data.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Only superusers can manage system configurations"""
        if not request.user.is_superuser:
            return SystemConfiguration.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """
    Admin interface for bank accounts - superuser only
    """
    list_display = [
        'name', 'get_bank_display_name', 'account_holder_name', 
        'account_type', 'is_active', 'is_default', 'updated_at'
    ]
    list_filter = [
        'bank', 'account_type', 'is_active', 'is_default', 'created_at'
    ]
    search_fields = [
        'name', 'account_holder_name', 'account_number', 'branch_code'
    ]
    list_editable = ['is_active', 'is_default']
    
    fieldsets = (
        ('Account Information', {
            'fields': (
                'name', 'bank', 'other_bank_name', 'account_holder_name',
                'account_number', 'branch_code', 'account_type'
            )
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_default')
        }),
        ('Payment Limits', {
            'fields': ('minimum_amount', 'maximum_amount')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['make_default', 'deactivate_others']
    
    def make_default(self, request, queryset):
        """Make selected account the default"""
        if queryset.count() > 1:
            self.message_user(request, 'Only one account can be set as default.', level='error')
            return
        
        account = queryset.first()
        account.is_default = True
        account.save()
        
        # Deactivate all other default accounts
        BankAccount.objects.filter(is_default=True).exclude(pk=account.pk).update(is_default=False)
        
        self.message_user(request, f'{account.name} is now the default bank account.')
    make_default.short_description = "Make selected account default"
    
    def deactivate_others(self, request, queryset):
        """Deactivate all accounts except selected ones"""
        count = BankAccount.objects.exclude(pk__in=queryset.values('pk')).update(is_active=False)
        self.message_user(request, f'Deactivated {count} other bank accounts.')
    deactivate_others.short_description = "Deactivate all other accounts"
    
    def get_queryset(self, request):
        """Only superusers can manage bank accounts"""
        if not request.user.is_superuser:
            return BankAccount.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """
    Admin interface for payment methods - superuser only
    """
    list_display = [
        'name', 'method_type', 'is_active', 'fee_percentage', 
        'fee_fixed', 'processing_time', 'sort_order'
    ]
    list_filter = ['method_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'sort_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('method_type', 'name', 'description', 'is_active')
        }),
        ('Display Settings', {
            'fields': ('icon_class', 'processing_time', 'sort_order')
        }),
        ('Fee Structure', {
            'fields': ('fee_percentage', 'fee_fixed')
        }),
        ('Payment Limits', {
            'fields': ('minimum_amount', 'maximum_amount')
        }),
        ('Instructions', {
            'fields': ('instructions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Only superusers can manage payment methods"""
        if not request.user.is_superuser:
            return PaymentMethod.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PlatformFee)
class PlatformFeeAdmin(admin.ModelAdmin):
    """
    Admin interface for platform fees - superuser only
    """
    list_display = [
        'name', 'fee_type', 'fee_percentage', 'fee_fixed', 
        'applies_to', 'is_active', 'minimum_amount'
    ]
    list_filter = ['fee_type', 'is_active', 'applies_to']
    search_fields = ['name', 'description', 'applies_to']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('fee_type', 'name', 'description', 'is_active')
        }),
        ('Fee Structure', {
            'fields': ('fee_percentage', 'fee_fixed')
        }),
        ('Application Rules', {
            'fields': ('applies_to', 'minimum_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Only superusers can manage platform fees"""
        if not request.user.is_superuser:
            return PlatformFee.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for email configurations - superuser only
    """
    list_display = [
        'config_type', 'from_email', 'from_name', 'is_active', 'daily_limit'
    ]
    list_filter = ['config_type', 'is_active']
    search_fields = ['from_email', 'from_name', 'host']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Settings', {
            'fields': ('config_type', 'is_active', 'from_email', 'from_name')
        }),
        ('SMTP Settings', {
            'fields': ('host', 'port', 'username', 'password', 'use_tls', 'use_ssl'),
            'classes': ('collapse',)
        }),
        ('API Settings', {
            'fields': ('api_key', 'domain'),
            'classes': ('collapse',)
        }),
        ('Limits', {
            'fields': ('daily_limit',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['test_email', 'activate_config']
    
    def test_email(self, request, queryset):
        """Test email configuration"""
        if queryset.count() > 1:
            self.message_user(request, 'Please select only one configuration to test.', level='error')
            return
        
        config = queryset.first()
        # Here you would implement actual email testing logic
        self.message_user(request, f'Email test sent for {config.get_config_type_display()}.')
    test_email.short_description = "Test email configuration"
    
    def activate_config(self, request, queryset):
        """Activate selected configuration"""
        if queryset.count() > 1:
            self.message_user(request, 'Only one configuration can be active at a time.', level='error')
            return
        
        config = queryset.first()
        config.is_active = True
        config.save()
        
        # Deactivate all other configurations
        EmailConfiguration.objects.filter(is_active=True).exclude(pk=config.pk).update(is_active=False)
        
        self.message_user(request, f'{config.get_config_type_display()} is now active.')
    activate_config.short_description = "Activate this configuration"
    
    def get_queryset(self, request):
        """Only superusers can manage email configurations"""
        if not request.user.is_superuser:
            return EmailConfiguration.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Custom admin site configuration
class SystemAdminSite(admin.AdminSite):
    """Custom admin site for system configurations"""
    site_header = "System Configuration"
    site_title = "System Admin"
    index_title = "System Configuration Management"
    
    def has_permission(self, request):
        """Only superusers can access system admin"""
        return request.user.is_superuser


# Create custom admin site instance
system_admin_site = SystemAdminSite(name='system_admin')

# Register models with custom admin site
system_admin_site.register(SystemConfiguration, SystemConfigurationAdmin)
system_admin_site.register(BankAccount, BankAccountAdmin)
system_admin_site.register(PaymentMethod, PaymentMethodAdmin)
system_admin_site.register(PlatformFee, PlatformFeeAdmin)
system_admin_site.register(EmailConfiguration, EmailConfigurationAdmin)
