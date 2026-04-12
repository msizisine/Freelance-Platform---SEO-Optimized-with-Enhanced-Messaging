from django.urls import path
from .views import (
    NotificationListView, NotificationDetailView, mark_notification_read,
    mark_all_notifications_read, delete_notification, notification_preferences,
    otp_login, otp_verify, sms_webhook, whatsapp_webhook, send_test_notification
)

app_name = 'notifications'

urlpatterns = [
    # Notification management
    path('', NotificationListView.as_view(), name='list'),
    path('<uuid:pk>/', NotificationDetailView.as_view(), name='detail'),
    path('<uuid:pk>/read/', mark_notification_read, name='mark_read'),
    path('mark-all-read/', mark_all_notifications_read, name='mark_all_read'),
    path('<uuid:pk>/delete/', delete_notification, name='delete'),
    
    # Preferences
    path('preferences/', notification_preferences, name='preferences'),
    
    # OTP Authentication
    path('login/', otp_login, name='otp_login'),
    path('verify/', otp_verify, name='otp_verify'),
    
    # Webhooks for SMS/WhatsApp
    path('webhook/sms/', sms_webhook, name='sms_webhook'),
    path('webhook/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
    
    # Testing
    path('test/', send_test_notification, name='test'),
]
