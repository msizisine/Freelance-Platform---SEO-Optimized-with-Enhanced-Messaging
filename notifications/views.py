from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from .models import Notification, OTPCode
from .services import NotificationService, OTPService


class NotificationListView(LoginRequiredMixin, ListView):
    """List all notifications for current user"""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """View notification details"""
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        )
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark as read when viewed
        self.object.mark_as_read()
        return response


@login_required
def mark_notification_read(request, pk):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


@login_required
def delete_notification(request, pk):
    """Delete notification"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Notification deleted.')
    return redirect('notifications:list')


@login_required
def notification_preferences(request):
    """View and update notification preferences"""
    from .models import NotificationPreference, Notification
    
    if request.method == 'POST':
        # Update preferences
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            preference, created = NotificationPreference.objects.get_or_create(
                user=request.user,
                notification_type=notification_type
            )
            
            preference.email_enabled = request.POST.get(f'email_{notification_type}', 'off') == 'on'
            preference.sms_enabled = request.POST.get(f'sms_{notification_type}', 'off') == 'on'
            preference.whatsapp_enabled = request.POST.get(f'whatsapp_{notification_type}', 'off') == 'on'
            preference.in_app_enabled = request.POST.get(f'in_app_{notification_type}', 'off') == 'on'
            preference.save()
        
        messages.success(request, 'Notification preferences updated successfully.')
        return redirect('notifications:preferences')
    
    # Get current preferences
    preferences = {}
    for notification_type, _ in Notification.NOTIFICATION_TYPES:
        pref, _ = NotificationPreference.objects.get_or_create(
            user=request.user,
            notification_type=notification_type
        )
        preferences[notification_type] = pref
    
    context = {
        'preferences': preferences,
        'notification_types': Notification.NOTIFICATION_TYPES,
    }
    
    return render(request, 'notifications/preferences.html', context)


def otp_login(request):
    """Login using OTP via SMS/WhatsApp"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, 'Please enter your phone number.')
            return render(request, 'notifications/otp_login.html')
        
        # Find user by phone number
        from core.models import User
        try:
            user = User.objects.get(phone=phone_number)
        except User.DoesNotExist:
            messages.error(request, 'No account found with this phone number.')
            return render(request, 'notifications/otp_login.html')
        
        # Generate and send OTP
        channel = request.POST.get('channel', 'sms')
        OTPService.generate_otp(user, phone_number, channel, 'login')
        
        # Store phone number in session for verification
        request.session['otp_phone'] = phone_number
        request.session['otp_channel'] = channel
        
        messages.success(request, f'Verification code sent to your {channel}.')
        return redirect('notifications:otp_verify')
    
    return render(request, 'notifications/otp_login.html')


def otp_verify(request):
    """Verify OTP code"""
    if 'otp_phone' not in request.session:
        return redirect('notifications:otp_login')
    
    if request.method == 'POST':
        code = request.POST.get('code')
        phone_number = request.session['otp_phone']
        
        if not code:
            messages.error(request, 'Please enter verification code.')
            return render(request, 'notifications/otp_verify.html')
        
        # Find user and verify OTP
        from core.models import User
        user = User.objects.get(phone=phone_number)
        
        if OTPService.verify_otp(user, code, 'login'):
            # Login user
            from django.contrib.auth import login
            login(request, user)
            
            # Clear session
            del request.session['otp_phone']
            del request.session['otp_channel']
            
            messages.success(request, 'Login successful!')
            return redirect('core:home')
        else:
            messages.error(request, 'Invalid or expired verification code.')
    
    return render(request, 'notifications/otp_verify.html')


@csrf_exempt
@require_http_methods(["POST"])
def sms_webhook(request):
    """Handle incoming SMS messages (for job acceptance, etc.)"""
    # Parse SMS data based on provider
    # This is a generic example - adjust based on your SMS provider
    
    # Example for Twilio
    from_phone = request.POST.get('From', '').replace('+', '')
    message_body = request.POST.get('Body', '')
    
    if from_phone and message_body:
        result = OTPService.handle_sms_response(from_phone, message_body)
        
        # Send response SMS if needed
        if result['status'] == 'error':
            # Send error message back
            from .services import SMSService
            SMSService.send_sms(
                from_phone,
                result['message'],
                {}
            )
    
    # Return Twilio response
    response = HttpResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>')
    response['Content-Type'] = 'text/xml'
    return response


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages"""
    # Parse WhatsApp data based on provider
    # This is a generic example - adjust based on your WhatsApp provider
    
    # Example for Twilio WhatsApp
    from_phone = request.POST.get('From', '').replace('whatsapp:', '').replace('+', '')
    message_body = request.POST.get('Body', '')
    
    if from_phone and message_body:
        result = OTPService.handle_sms_response(from_phone, message_body)
        
        # Send response WhatsApp message if needed
        if result['status'] == 'error':
            from .services import WhatsAppService
            WhatsAppService.send_whatsapp(
                from_phone,
                result['message'],
                {}
            )
    
    # Return Twilio response
    response = HttpResponse('<?xml version="1.0" encoding="UTF-8"?><Response></Response>')
    response['Content-Type'] = 'text/xml'
    return response


@login_required
def send_test_notification(request):
    """Send test notification (for development/testing)"""
    if request.method == 'POST':
        notification_type = request.POST.get('notification_type', 'message_received')
        title = request.POST.get('title', 'Test Notification')
        message = request.POST.get('message', 'This is a test notification.')
        channels = request.POST.getlist('channels')
        
        NotificationService.send_notification(
            recipient=request.user,
            notification_type=notification_type,
            title=title,
            message=message,
            channels=channels
        )
        
        messages.success(request, 'Test notification sent!')
        return redirect('notifications:test')
    
    return render(request, 'notifications/test.html', {
        'notification_types': Notification.NOTIFICATION_TYPES,
        'channels': Notification.CHANNELS,
    })
