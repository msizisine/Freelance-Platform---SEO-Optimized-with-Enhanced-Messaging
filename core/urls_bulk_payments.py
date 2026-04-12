"""
URL patterns for bulk payment processing
"""
from django.urls import path
from core.views_bulk_payments import (
    BulkPaymentDashboardView,
    GenerateBulkPaymentView,
    PayoutSelectionView,
    BatchDetailView,
    UpdateBatchStatusView,
    DownloadBatchCSVView,
)

app_name = 'bulk_payments'

urlpatterns = [
    # Bulk Payment Dashboard
    path('dashboard/', BulkPaymentDashboardView.as_view(), name='bulk_payment_dashboard'),
    
    # Payout Selection
    path('select/', PayoutSelectionView.as_view(), name='payout_selection'),
    
    # Generate Bulk Payment
    path('generate/', GenerateBulkPaymentView.as_view(), name='generate_bulk_payment'),
    
    # Batch Detail
    path('batch/<uuid:pk>/', BatchDetailView.as_view(), name='batch_detail'),
    
    # Update Batch Status
    path('batch/<uuid:pk>/update/', UpdateBatchStatusView.as_view(), name='update_batch_status'),
    
    # Download Batch CSV
    path('batch/<uuid:pk>/download/', DownloadBatchCSVView.as_view(), name='download_batch_csv'),
]
