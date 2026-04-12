from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import redirect
from whatsapp_webhook import whatsapp_webhook
from gigs.sitemaps import GigSitemap, CategorySitemap, StaticSitemap, ProviderSitemap

def redirect_to_receipts(request):
    """Redirect old admin/receipts URL to new system/receipts URL"""
    return redirect('/system/receipts/')

urlpatterns = [
    path('admin/receipts/', redirect_to_receipts),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),  # Add custom users routes
    path('', include('core.urls')),
    path('gigs/', include('gigs.urls')),
    path('orders/', include('orders.urls')),
    path('messages/', include('messaging.urls')),  # Updated to messaging
    path('reviews/', include('reviews.urls')),
    path('notifications/', include('notifications.urls')),
    path('webhook/whatsapp/', include('gigs.webhook_urls')),  # WhatsApp webhooks
    path('api/whatsapp/webhook/', whatsapp_webhook),  # Direct WhatsApp webhook
    
    # SEO URLs
    path('sitemap.xml', sitemap, {
        'sitemaps': {
            'gigs': GigSitemap,
            'categories': CategorySitemap,
            'providers': ProviderSitemap,
            'static': StaticSitemap,
        }
    }, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]  # Temporarily disabled
