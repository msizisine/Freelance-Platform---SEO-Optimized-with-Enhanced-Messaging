"""
URL configuration for new features
"""
from django.urls import path
from django.views.generic import TemplateView
from . import views_search, views_features

app_name = 'core'

urlpatterns = [
    # Advanced Search
    path('search/', views_search.advanced_search, name='advanced_search'),
    path('search/suggestions/', views_search.search_suggestions, name='search_suggestions'),
    path('search/recommendations/', views_search.search_recommendations, name='search_recommendations'),
    
    # Saved Searches
    path('search/saved/', views_search.saved_searches, name='saved_searches'),
    path('search/save/', views_search.save_search, name='save_search'),
    path('search/delete/<int:search_id>/', views_search.delete_saved_search, name='delete_saved_search'),
    
    # Portfolio
    path('portfolio/', views_features.portfolio_list, name='portfolio_list'),
    path('portfolio/<int:user_id>/', views_features.portfolio_list, name='portfolio_list_user'),
    path('portfolio/create/', views_features.PortfolioCreateView.as_view(), name='portfolio_create'),
    path('portfolio/<uuid:pk>/edit/', views_features.PortfolioUpdateView.as_view(), name='portfolio_edit'),
    path('portfolio/<uuid:item_id>/delete/', views_features.portfolio_delete, name='portfolio_delete'),
    
    # Reviews
    path('review/create/<int:provider_id>/', views_features.ReviewCreateView.as_view(), name='review_create'),
    path('review/<int:review_id>/helpful/', views_features.review_helpful, name='review_helpful'),
    
    # Availability Calendar
    path('availability/', views_features.availability_calendar, name='availability_calendar'),
    path('availability/<int:user_id>/', views_features.availability_calendar, name='availability_calendar_user'),
    path('availability/slot/create/', views_features.availability_slot_create, name='availability_slot_create'),
    path('availability/slot/<int:slot_id>/update/', views_features.availability_slot_update, name='availability_slot_update'),
    
    # Invoices
    path('invoices/', views_features.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views_features.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<uuid:invoice_id>/', views_features.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:invoice_id>/pdf/', views_features.invoice_generate_pdf, name='invoice_generate_pdf'),
    
    # Disputes
    path('disputes/', views_features.DisputeListView.as_view(), name='dispute_list'),
    path('disputes/create/', views_features.DisputeCreateView.as_view(), name='dispute_create'),
    path('disputes/<uuid:dispute_id>/', views_features.dispute_detail, name='dispute_detail'),
    path('disputes/<uuid:dispute_id>/message/', views_features.dispute_message_create, name='dispute_message_create'),
    
    # Analytics Dashboard
    path('analytics/', views_features.analytics_dashboard, name='analytics_dashboard'),
    
    # SEO and Sitemaps
]
