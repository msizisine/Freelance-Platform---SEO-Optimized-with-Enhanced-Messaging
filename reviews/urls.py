from django.urls import path
from .views import ReviewCreateView, ReviewDetailView, review_response_create, toggle_helpful_vote, freelancer_reviews, homeowner_reviews
from .views_invoice import create_review_with_invoice, thank_you

app_name = 'reviews'

urlpatterns = [
    path('create/<uuid:order_id>/', ReviewCreateView.as_view(), name='create'),
    path('create-with-invoice/<int:user_id>/<uuid:order_id>/<int:job_id>/', create_review_with_invoice, name='create_review_with_invoice'),
    path('<int:pk>/', ReviewDetailView.as_view(), name='detail'),
    path('<int:pk>/respond/', review_response_create, name='respond'),
    path('<int:pk>/helpful/', toggle_helpful_vote, name='helpful'),
    path('freelancer/<int:user_id>/', freelancer_reviews, name='freelancer_reviews'),
    path('homeowner/<int:user_id>/', homeowner_reviews, name='homeowner_reviews'),
    path('thank-you/', thank_you, name='thank_you'),
]
