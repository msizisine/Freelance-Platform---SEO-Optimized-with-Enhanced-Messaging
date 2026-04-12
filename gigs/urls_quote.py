"""
URL patterns for Quote Request System with WhatsApp Integration
"""
from django.urls import path
from . import views_quote

app_name = 'quotes'

urlpatterns = [
    # Quote Request Views
    path('request/<int:gig_id>/whatsapp/', views_quote.request_quote_via_whatsapp, name='request_via_whatsapp'),
    path('request-whatsapp-bulk/', views_quote.request_quote_via_whatsapp_bulk, name='request_whatsapp_bulk'),
    path('list/', views_quote.QuoteRequestListView.as_view(), name='quote_request_list'),
    path('<uuid:pk>/', views_quote.QuoteRequestDetailView.as_view(), name='quote_request_detail'),
    path('<uuid:quote_request_id>/respond/', views_quote.QuoteResponseCreateView.as_view(), name='quote_response_create'),
    
    # WhatsApp Webhook
    path('webhook/whatsapp/', views_quote.whatsapp_webhook, name='whatsapp_webhook'),
    
    # Actions
    path('<uuid:quote_request_id>/resend-whatsapp/', views_quote.resend_quote_request_whatsapp, name='resend_whatsapp'),
    path('accept/<int:response_id>/', views_quote.accept_quote_response, name='accept_response'),
    
    # Analytics
    path('analytics/', views_quote.quote_analytics, name='analytics'),
]
