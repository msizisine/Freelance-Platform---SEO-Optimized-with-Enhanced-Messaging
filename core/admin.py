from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

# Import payment admin configurations
from .admin_payments import (
    ProviderEarningsAdmin, ProviderPayoutAdmin, 
    MonthlyServiceFeeAdmin, PaymentTransactionAdmin
)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    model = User

    list_display = ('email', 'user_type', 'is_staff', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('user_type', 'profile_picture', 'bio', 'location', 'website')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
