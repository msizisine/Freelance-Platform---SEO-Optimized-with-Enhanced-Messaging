from django.urls import path
from django.views.generic import TemplateView
from .views import HomeView, SearchView, AdminServiceProviderListView, AdminServiceProviderDetailView, verify_service_provider, unverify_service_provider
from .views_admin import create_superuser_view
from .views_migrate import run_migrations
from .views_logout import custom_logout
from .views_config import (
    SystemConfigurationListView, SystemConfigurationUpdateView,
    BankAccountListView, PaymentMethodListView, PlatformFeeListView,
    EmailConfigurationListView, system_dashboard
)
from .views_payments import (
    ProviderEarningsListView, ProviderPayoutCreateView, ProviderPayoutListView,
    ProviderTransactionListView, payout_dashboard, AdminPayoutManagementView,
    approve_payout, complete_payout, reject_payout, generate_monthly_fees, all_transactions, manage_earnings,
    download_payout_history_csv, download_payout_requests_csv
)
from .views_receipts import receipt_transaction_list, payment_receipt_dashboard
from .views_provider_bank import (
    ProviderBankAccountListView, ProviderBankAccountCreateView, ProviderBankAccountUpdateView,
    ProviderBankAccountDetailView, PayoutRequestListView, PayoutRequestCreateView,
    AdminBankAccountListView, AdminBankAccountDetailView,
    set_default_bank_account, delete_bank_account, verify_bank_account, reject_bank_account
)
from .views_bulk_payments import (
    BulkPaymentDashboardView, GenerateBulkPaymentView, PayoutSelectionView,
    BatchDetailView, UpdateBatchStatusView, DownloadBatchCSVView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('search/', SearchView.as_view(), name='search'),
    path('logout/', custom_logout, name='custom_logout'),
    # Admin verification URLs
    path('admin-providers/', AdminServiceProviderListView.as_view(), name='admin_provider_list'),
    path('admin-providers/<int:pk>/', AdminServiceProviderDetailView.as_view(), name='admin_provider_detail'),
    path('admin-providers/<int:pk>/verify/', verify_service_provider, name='admin_verify_provider'),
    path('admin-providers/<int:pk>/unverify/', unverify_service_provider, name='admin_unverify_provider'),
    # System configuration URLs
    path('system/', system_dashboard, name='system_dashboard'),
    path('system/config/', SystemConfigurationListView.as_view(), name='system_config_list'),
    path('system/config/<int:pk>/edit/', SystemConfigurationUpdateView.as_view(), name='system_config_edit'),
    path('system/bank-accounts/', BankAccountListView.as_view(), name='bank_account_list'),
    path('system/payment-methods/', PaymentMethodListView.as_view(), name='payment_method_list'),
    path('system/platform-fees/', PlatformFeeListView.as_view(), name='platform_fee_list'),
    path('system/email-configs/', EmailConfigurationListView.as_view(), name='email_config_list'),
    # Payment processing URLs
    path('payments/dashboard/', payout_dashboard, name='payout_dashboard'),
    path('payments/admin/payouts/', AdminPayoutManagementView.as_view(), name='admin_payout_management'),
    path('payments/admin/transactions/', all_transactions, name='all_transactions'),
    path('payments/admin/earnings/', manage_earnings, name='manage_earnings'),
    path('payments/admin/generate-fees/', generate_monthly_fees, name='generate_monthly_fees'),
    path('payments/payout/request/', ProviderPayoutCreateView.as_view(), name='payout_request'),
    path('payments/payouts/', ProviderPayoutListView.as_view(), name='payout_list'),
    path('payments/earnings/', ProviderEarningsListView.as_view(), name='provider_earnings'),
    path('payments/transactions/', ProviderTransactionListView.as_view(), name='transaction_history'),
    path('payments/payout/<uuid:pk>/approve/', approve_payout, name='approve_payout'),
    path('payments/payout/<uuid:pk>/complete/', complete_payout, name='complete_payout'),
    path('payments/payout/<uuid:pk>/reject/', reject_payout, name='reject_payout'),
    path('payments/admin/download/payout-history-csv/', download_payout_history_csv, name='download_payout_history_csv'),
    path('payments/admin/download/payout-requests-csv/', download_payout_requests_csv, name='download_payout_requests_csv'),
    # Payment receipt URLs
    path('system/receipts/', receipt_transaction_list, name='receipt_transactions'),
    path('system/receipts/dashboard/', payment_receipt_dashboard, name='receipt_dashboard'),
    # Provider bank account URLs
    path('bank-accounts/', ProviderBankAccountListView.as_view(), name='bank_account_list'),
    path('bank-accounts/add/', ProviderBankAccountCreateView.as_view(), name='bank_account_create'),
    path('bank-accounts/<uuid:pk>/', ProviderBankAccountDetailView.as_view(), name='bank_account_detail'),
    path('bank-accounts/<uuid:pk>/edit/', ProviderBankAccountUpdateView.as_view(), name='bank_account_edit'),
    path('bank-accounts/<uuid:pk>/set-default/', set_default_bank_account, name='bank_account_set_default'),
    path('bank-accounts/<uuid:pk>/delete/', delete_bank_account, name='bank_account_delete'),
    # Payout request URLs
    path('payout-requests/', PayoutRequestListView.as_view(), name='payout_request_list'),
    path('payout-requests/request/', PayoutRequestCreateView.as_view(), name='payout_request_create'),
    # Admin bank account management URLs
    path('admin/provider-bank-accounts/', AdminBankAccountListView.as_view(), name='admin_provider_bank_accounts'),
    path('admin/provider-bank-accounts/<uuid:pk>/', AdminBankAccountDetailView.as_view(), name='admin_provider_bank_account_detail'),
    path('admin/provider-bank-accounts/<uuid:pk>/verify/', verify_bank_account, name='admin_verify_bank_account'),
    path('admin/provider-bank-accounts/<uuid:pk>/reject/', reject_bank_account, name='admin_reject_bank_account'),
    
    # Bulk Payment Processing URLs
    path('admin/bulk-payments/', BulkPaymentDashboardView.as_view(), name='bulk_payment_dashboard'),
    path('admin/bulk-payments/select/', PayoutSelectionView.as_view(), name='payout_selection'),
    path('admin/bulk-payments/generate/', GenerateBulkPaymentView.as_view(), name='generate_bulk_payment'),
    path('admin/bulk-payments/batch/<uuid:pk>/', BatchDetailView.as_view(), name='batch_detail'),
    path('admin/bulk-payments/batch/<uuid:pk>/update/', UpdateBatchStatusView.as_view(), name='update_batch_status'),
    path('admin/bulk-payments/batch/<uuid:pk>/download/', DownloadBatchCSVView.as_view(), name='download_batch_csv'),
    
    # Support Pages URLs
    path('help/', TemplateView.as_view(template_name='core/help_center.html'), name='help_center'),
    path('safety/', TemplateView.as_view(template_name='core/safety_tips.html'), name='safety_tips'),
    path('terms/', TemplateView.as_view(template_name='core/terms_of_service.html'), name='terms_of_service'),
    path('privacy/', TemplateView.as_view(template_name='core/privacy_policy.html'), name='privacy_policy'),
    path('contact/', TemplateView.as_view(template_name='core/contact_us.html'), name='contact_us'),
    
    # PWA URLs
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('service-worker.js', TemplateView.as_view(template_name='service-worker.js', content_type='application/javascript'), name='service_worker'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    
    # Temporary: Database setup - REMOVE IN PRODUCTION
    path('migrate/', run_migrations, name='run_migrations'),
    
    ]
