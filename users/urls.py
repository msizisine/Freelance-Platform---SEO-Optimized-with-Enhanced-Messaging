from django.urls import path
from .views import ProfileView, ProfileUpdateView, portfolio_create, portfolio_edit, portfolio_delete, dashboard, my_profile, reference_create, reference_delete, portfolio_view, user_reviews, send_message
from .views_signup import CustomSignupView

app_name = 'users'

urlpatterns = [
    path('signup/', CustomSignupView.as_view(), name='signup'),
    path('signup/profile/', ProfileUpdateView.as_view(), name='signup_profile_edit'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', my_profile, name='my_profile'),
    path('profile/<int:pk>/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('send-message/<int:user_id>/', send_message, name='send_message'),
    path('portfolio/add/', portfolio_create, name='portfolio_create'),
    path('portfolio/<int:pk>/edit/', portfolio_edit, name='portfolio_edit'),
    path('portfolio/<int:pk>/delete/', portfolio_delete, name='portfolio_delete'),
    path('portfolio/<int:user_id>/', portfolio_view, name='portfolio_view'),
    path('reference/add/', reference_create, name='reference_create'),
    path('reference/<int:pk>/delete/', reference_delete, name='reference_delete'),
    path('reviews/<int:user_id>/', user_reviews, name='user_reviews'),
]
