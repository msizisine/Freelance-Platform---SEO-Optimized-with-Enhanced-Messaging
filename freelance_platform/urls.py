"""
Simplified URL configuration for Railway to prevent redirect loops
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),  # Only include core.urls once
    path('users/', include('users.urls')),
    path('gigs/', include('gigs.urls')),
    path('orders/', include('orders.urls')),
    path('messages/', include('messaging.urls')),
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
]

# Add static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
