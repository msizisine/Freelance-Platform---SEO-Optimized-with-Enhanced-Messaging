from django.contrib import admin
from .models import Order, OrderFile, OrderMessage, OrderRevision, OrderDispute, OrderTracking


class OrderFileInline(admin.TabularInline):
    model = Order.delivery_files.through
    extra = 1


class OrderMessageInline(admin.TabularInline):
    model = OrderMessage
    extra = 0
    readonly_fields = ('created_at',)


class OrderRevisionInline(admin.TabularInline):
    model = OrderRevision
    extra = 0
    readonly_fields = ('created_at',)


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'homeowner', 'service_provider', 'gig', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'client__email', 'freelancer__email', 'gig__title')
    readonly_fields = ('order_number', 'created_at', 'accepted_at', 'completed_at')
    inlines = [OrderMessageInline, OrderRevisionInline, OrderTrackingInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'client', 'freelancer', 'gig', 'package')
        }),
        ('Order Details', {
            'fields': ('requirements', 'total_amount', 'delivery_days', 'due_date')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Payment', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'accepted_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderFile)
class OrderFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'uploaded_by', 'uploaded_at')
    search_fields = ('filename', 'uploaded_by__email')


@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    list_display = ('order', 'sender', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__order_number', 'sender__email', 'message')


@admin.register(OrderRevision)
class OrderRevisionAdmin(admin.ModelAdmin):
    list_display = ('order', 'requested_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'requested_by__email', 'reason')


@admin.register(OrderDispute)
class OrderDisputeAdmin(admin.ModelAdmin):
    list_display = ('order', 'raised_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'raised_by__email', 'reason')
    
    fieldsets = (
        ('Dispute Information', {
            'fields': ('order', 'raised_by', 'reason', 'description', 'status')
        }),
        ('Admin', {
            'fields': ('admin_notes', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('order__order_number', 'notes')
    readonly_fields = ('timestamp',)
