from django.urls import path, include
from .views import (
    OrderListView, OrderDetailView, OrderCreateView, payment_view, payment_confirmation,
    add_order_message, accept_order, reject_order, start_order_progress,
    deliver_order, request_revision, complete_order, cancel_order, process_payment_view, payment_thank_you_view,
    payfast_payment_view, yoco_payment_view, eft_payment_view, ozow_payment_view, confirm_eft_payment
)
from .create_order_from_provider import create_order_from_provider
from .create_private_job import create_private_job
from . import job_offer_views
from .ozow_notification_handler import ozow_notification_handler

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('create/<int:gig_id>/', OrderCreateView.as_view(), name='create'),
    path('create-from-provider/<int:provider_id>/', create_order_from_provider, name='create_from_provider'),
    path('create-job/', create_order_from_provider, name='create_job'),
    path('create-private-job/<int:provider_id>/', create_private_job, name='create_private_job'),
    
    # Job offer URLs
    path('job-offers/received/', job_offer_views.job_offers_received, name='job_offers_received'),
    path('job-offers/sent/', job_offer_views.job_offers_sent, name='job_offers_sent'),
    path('job-offers/<uuid:offer_id>/submit-estimate/', job_offer_views.submit_estimate, name='submit_estimate'),
    path('job-offers/review-estimates/', job_offer_views.review_estimates, name='review_estimates'),
    path('job-offers/<uuid:offer_id>/approve/', job_offer_views.approve_estimate, name='approve_estimate'),
    path('job-offers/<uuid:offer_id>/decline/', job_offer_views.decline_estimate, name='decline_estimate'),
    
    path('<uuid:pk>/', OrderDetailView.as_view(), name='detail'),
    path('<uuid:pk>/payment/', payment_view, name='payment'),
    path('<uuid:pk>/payment/confirm/', payment_confirmation, name='payment_confirm'),
    path('<uuid:pk>/process-payment/', process_payment_view, name='process_payment'),
    path('<uuid:pk>/payment/thank-you/', payment_thank_you_view, name='payment_thank_you'),
    path('<uuid:pk>/message/', add_order_message, name='add_message'),
    path('<uuid:pk>/accept/', accept_order, name='accept'),
    path('<uuid:pk>/reject/', reject_order, name='reject'),
    path('<uuid:pk>/start/', start_order_progress, name='start_progress'),
    path('<uuid:pk>/deliver/', deliver_order, name='deliver'),
    path('<uuid:pk>/revision/', request_revision, name='request_revision'),
    path('<uuid:pk>/complete/', complete_order, name='complete'),
    path('<uuid:pk>/cancel/', cancel_order, name='cancel'),
    
    # South African Payment Methods
    path('<uuid:pk>/payfast/', payfast_payment_view, name='payfast_payment'),
    path('<uuid:pk>/yoco/', yoco_payment_view, name='yoco_payment'),
    path('<uuid:pk>/ozow/', ozow_payment_view, name='ozow_payment'),
    path('<uuid:pk>/ozow-notify/', ozow_notification_handler, name='ozow_notify'),
    path('<uuid:pk>/eft/', eft_payment_view, name='eft_payment'),
    path('<uuid:pk>/eft/confirm/', confirm_eft_payment, name='confirm_eft_payment'),
]
