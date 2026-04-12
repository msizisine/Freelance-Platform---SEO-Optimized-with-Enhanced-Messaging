"""
Webhook URLs for WhatsApp integration
"""
from django.urls import path
from . import webhooks

app_name = 'webhooks'

urlpatterns = [
    path('', webhooks.whatsapp_webhook, name='whatsapp_webhook'),
]
