"""
Admin interface for dynamic configurations - superuser only
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.forms import Textarea, JSONField
from django.db import models
from .models_dynamic_config import (
    DynamicConfiguration, ConfigurationHistory, ConfigurationTemplate
)


class DynamicConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for dynamic configurations - superuser only
    """
    list_display = [
        'name', 'key', 'category', 'data_type', 'get_display_value', 
        'is_active', 'is_required', 'last_modified_at'
    ]
    list_filter = [
        'category', 'data_type', 'is_active', 'is_required', 'is_public', 'created_at'
    ]
    search_fields = ['key', 'name', 'description']
    list_editable = ['is_active', 'is_required']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'key', 'name', 'category', 'data_type', 'description'
            )
        }),
        ('Configuration Value', {
            'fields': (
                ('value', 'encrypted_value'),
                'default_value'
            ),
            'description': 'Enter configuration value. Encrypted data will be stored securely.'
        }),
        ('Validation & Constraints', {
            'fields': (
                'is_required',
                'validation_rules',
                ('is_public', 'is_editable'),
                'requires_restart'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Audit', {
            'fields': (
                'is_active',
                'version',
                'last_modified_by',
                'last_modified_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['last_modified_by', 'last_modified_at', 'version']
    
    actions = [
        'reset_to_default', 'export_configs', 'activate_configs', 
        'deactivate_configs', 'validate_configs'
    ]
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 80})},
    }
    
    def get_queryset(self, request):
        """Only superusers can manage dynamic configurations"""
        if not request.user.is_superuser:
            return DynamicConfiguration.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Set last modified by and track history"""
        obj.last_modified_by = request.user
        
        if change:
            # Track the old value for history
            old_obj = DynamicConfiguration.objects.get(pk=obj.pk)
            old_value = old_obj.get_value()
            new_value = obj.get_value()
            
            if old_value != new_value:
                from .models_dynamic_config import ConfigurationHistory
                ConfigurationHistory.objects.create(
                    configuration=obj,
                    old_value=str(old_value) if old_value is not None else '',
                    new_value=str(new_value) if new_value is not None else '',
                    changed_by=request.user,
                    change_reason='Configuration updated via admin'
                )
        
        super().save_model(request, obj, form, change)
    
    def reset_to_default(self, request, queryset):
        """Reset selected configurations to default values"""
        count = 0
        for config in queryset:
            if config.default_value:
                config.reset_to_default()
                count += 1
        self.message_user(request, f'Reset {count} configurations to default values.')
    reset_to_default.short_description = "Reset to default values"
    
    def export_configs(self, request, queryset):
        """Export configurations as JSON"""
        import json
        from django.http import HttpResponse
        
        configs = {}
        for config in queryset:
            configs[config.key] = {
                'value': config.get_value(),
                'data_type': config.data_type,
                'category': config.category,
                'name': config.name,
                'description': config.description
            }
        
        response = HttpResponse(
            json.dumps(configs, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="configurations.json"'
        return response
    export_configs.short_description = "Export configurations as JSON"
    
    def activate_configs(self, request, queryset):
        """Activate selected configurations"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Activated {count} configurations.')
    activate_configs.short_description = "Activate selected"
    
    def deactivate_configs(self, request, queryset):
        """Deactivate selected configurations"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} configurations.')
    deactivate_configs.short_description = "Deactivate selected"
    
    def validate_configs(self, request, queryset):
        """Validate selected configurations"""
        errors = []
        valid_count = 0
        
        for config in queryset:
            try:
                config.clean()
                valid_count += 1
            except Exception as e:
                errors.append(f"{config.key}: {str(e)}")
        
        if errors:
            self.message_user(
                request, 
                f"Validation errors found: {'; '.join(errors)}", 
                level='error'
            )
        else:
            self.message_user(request, f'All {valid_count} configurations are valid.')
    validate_configs.short_description = "Validate configurations"


class ConfigurationHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for configuration history - superuser only
    """
    list_display = [
        'configuration', 'get_old_value', 'get_new_value', 
        'changed_by', 'changed_at', 'change_reason'
    ]
    list_filter = [
        'configuration__category', 'changed_at', 'changed_by'
    ]
    search_fields = [
        'configuration__key', 'configuration__name', 'change_reason'
    ]
    readonly_fields = [
        'configuration', 'old_value', 'new_value', 
        'changed_by', 'changed_at'
    ]
    
    def get_queryset(self, request):
        """Only superusers can view configuration history"""
        if not request.user.is_superuser:
            return ConfigurationHistory.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return False  # History is created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # History should not be changed
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_old_value(self, obj):
        """Display old value with formatting"""
        if not obj.old_value:
            return "None"
        return obj.old_value[:100] + "..." if len(obj.old_value) > 100 else obj.old_value
    get_old_value.short_description = "Old Value"
    
    def get_new_value(self, obj):
        """Display new value with formatting"""
        if not obj.new_value:
            return "None"
        return obj.new_value[:100] + "..." if len(obj.new_value) > 100 else obj.new_value
    get_new_value.short_description = "New Value"


class ConfigurationTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for configuration templates - superuser only
    """
    list_display = [
        'name', 'category', 'description', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'is_active')
        }),
        ('Template Configurations', {
            'fields': ('configurations',),
            'description': 'JSON array of configuration objects'
        })
    )
    
    actions = ['apply_template']
    
    def get_queryset(self, request):
        """Only superusers can manage configuration templates"""
        if not request.user.is_superuser:
            return ConfigurationTemplate.objects.none()
        return super().get_queryset(request)
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def apply_template(self, request, queryset):
        """Apply selected template to create configurations"""
        total_created = 0
        for template in queryset:
            try:
                created = template.apply_template(user=request.user)
                total_created += created
                self.message_user(
                    request, 
                    f"Applied template '{template.name}' - created {created} configurations."
                )
            except Exception as e:
                self.message_user(
                    request, 
                    f"Error applying template '{template.name}': {str(e)}", 
                    level='error'
                )
    apply_template.short_description = "Apply template to create configurations"


# Register models with admin
admin.site.register(DynamicConfiguration, DynamicConfigurationAdmin)
admin.site.register(ConfigurationHistory, ConfigurationHistoryAdmin)
admin.site.register(ConfigurationTemplate, ConfigurationTemplateAdmin)
