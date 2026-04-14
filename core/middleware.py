from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponse
import gzip
from io import BytesIO
import re


class GZipMiddleware(MiddlewareMixin):
    """Middleware to compress response content with Gzip"""
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.compressible_types = {
            'text/html',
            'text/css', 
            'text/javascript',
            'text/xml',
            'application/javascript',
            'application/json',
            'application/xml',
            'text/plain',
        }
    
    def process_response(self, request, response):
        # Only compress if client accepts gzip
        if not self.should_compress(request, response):
            return response
        
        # Compress the content
        compressed_content = self.compress_content(response.content)
        
        # Update response headers
        response.content = compressed_content
        response['Content-Encoding'] = 'gzip'
        response['Content-Length'] = str(len(compressed_content))
        
        # Remove ETag as content has changed
        if 'ETag' in response:
            del response['ETag']
        
        return response
    
    def should_compress(self, request, response):
        """Check if response should be compressed"""
        # Check if client accepts gzip
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if 'gzip' not in accept_encoding.lower():
            return False
        
        # Check content type
        content_type = response.get('Content-Type', '').split(';')[0]
        if content_type not in self.compressible_types:
            return False
        
        # Don't compress if already compressed
        if response.get('Content-Encoding') == 'gzip':
            return False
        
        # Don't compress small files (less than 1KB)
        if len(response.content) < 1024:
            return False
        
        # Don't compress if response status indicates no content
        if response.status_code in (204, 304):
            return False
        
        return True
    
    def compress_content(self, content):
        """Compress content using gzip"""
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb', compresslevel=6) as gz_file:
            gz_file.write(content)
        return buffer.getvalue()


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers for better SEO and security"""
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add HSTS for HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Add Content Security Policy (basic version)
        if not response.get('Content-Security-Policy'):
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://www.google-analytics.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://www.google-analytics.com; "
                "frame-ancestors 'none';"
            )
            response['Content-Security-Policy'] = csp
        
        return response


class PerformanceHeadersMiddleware(MiddlewareMixin):
    """Middleware to add performance optimization headers"""
    
    def process_response(self, request, response):
        # Add cache control headers for static content
        if self.is_static_content(request.path):
            cache_duration = 31536000  # 1 year
            response['Cache-Control'] = f'public, max-age={cache_duration}'
            response['Expires'] = self.get_expires_header(cache_duration)
        
        # Add cache control for HTML pages
        elif response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'public, max-age=3600, must-revalidate'
        
        # Add ETag for cache validation
        if not response.get('ETag') and response.content:
            etag = self.generate_etag(response.content)
            response['ETag'] = etag
        
        return response
    
    def is_static_content(self, path):
        """Check if request is for static content"""
        static_patterns = [
            r'^/static/',
            r'^/media/',
            r'\.css$',
            r'\.js$',
            r'\.png$',
            r'\.jpg$',
            r'\.jpeg$',
            r'\.gif$',
            r'\.webp$',
            r'\.svg$',
            r'\.ico$',
            r'\.woff2?$',
        ]
        
        for pattern in static_patterns:
            if re.search(pattern, path):
                return True
        return False
    
    def generate_etag(self, content):
        """Generate ETag for content"""
        import hashlib
        return f'"{hashlib.md5(content).hexdigest()}"'
    
    def get_expires_header(self, seconds):
        """Generate Expires header"""
        from datetime import datetime, timedelta
        expires = datetime.utcnow() + timedelta(seconds=seconds)
        return expires.strftime('%a, %d %b %Y %H:%M:%S GMT')


class SEOHeadersMiddleware(MiddlewareMixin):
    """Middleware to add SEO-related headers"""
    
    def process_response(self, request, response):
        # Add canonical URL if not present
        if response.get('Content-Type', '').startswith('text/html'):
            if not response.get('Link') or 'canonical' not in response.get('Link', ''):
                canonical_url = request.build_absolute_uri()
                response['Link'] = f'<{canonical_url}>; rel="canonical"'
        
        return response


class RemoveUnnecessaryHeadersMiddleware(MiddlewareMixin):
    """Middleware to remove unnecessary headers for security and performance"""
    
    def process_response(self, request, response):
        # Remove server header for security
        if 'Server' in response:
            del response['Server']
        
        # Remove X-Powered-By header
        if 'X-Powered-By' in response:
            del response['X-Powered-By']
        
        return response


class DatabaseOptimizationMiddleware(MiddlewareMixin):
    """Middleware to optimize database queries"""
    
    def process_request(self, request):
        """Optimize database queries for common requests"""
        # Prefetch commonly accessed data for authenticated users
        if request.user.is_authenticated:
            # This would be implemented in views, but middleware can help
            pass
    
    def process_response(self, request, response):
        """Add database query statistics in debug mode"""
        if settings.DEBUG:
            from django.db import connection
            query_count = len(connection.queries)
            response['X-DB-Queries'] = str(query_count)
        
        return response


class ImageOptimizationMiddleware(MiddlewareMixin):
    """Middleware to optimize images on the fly"""
    
    def process_response(self, request, response):
        # This would integrate with the image optimization templatetags
        # For now, just add headers for image optimization
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Add headers for better image caching
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            
            # Add Vary header for proper caching
            response['Vary'] = 'Accept-Encoding'
        
        return response


class ContentDeliveryMiddleware(MiddlewareMixin):
    """Middleware to optimize content delivery"""
    
    def process_response(self, request, response):
        # Add preconnect headers for external resources
        if response.get('Content-Type', '').startswith('text/html'):
            preconnect_urls = [
                'https://cdn.jsdelivr.net',
                'https://fonts.googleapis.com',
                'https://fonts.gstatic.com',
            ]
            
            preconnect_link = ''
            for url in preconnect_urls:
                preconnect_link += f'<{url}>; rel="preconnect", '
            
            if preconnect_link:
                existing_link = response.get('Link', '')
                response['Link'] = preconnect_link.rstrip(', ') + (', ' + existing_link if existing_link else '')
        
        return response


# Middleware configuration helper
def get_performance_middleware():
    """Get the recommended middleware stack for performance"""
    return [
        'core.middleware.RemoveUnnecessaryHeadersMiddleware',
        'core.middleware.SecurityHeadersMiddleware',
        'core.middleware.PerformanceHeadersMiddleware',
        'core.middleware.SEOHeadersMiddleware',
        'core.middleware.GZipMiddleware',
        'core.middleware.ContentDeliveryMiddleware',
        'core.middleware.ImageOptimizationMiddleware',
    ]


# Performance monitoring
class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.start_time = None
        self.query_count = 0
    
    def start_timing(self):
        """Start timing the request"""
        import time
        self.start_time = time.time()
    
    def end_timing(self, request, response):
        """End timing and log performance"""
        if self.start_time:
            import time
            duration = time.time() - self.start_time
            
            # Log slow requests
            if duration > 1.0:  # More than 1 second
                import logging
                logger = logging.getLogger('performance')
                logger.warning(
                    f'Slow request: {request.path} took {duration:.2f}s '
                    f'with {self.query_count} DB queries'
                )
    
    def log_query_count(self):
        """Log database query count"""
        from django.db import connection
        self.query_count = len(connection.queries)


# Performance monitoring middleware
class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware to monitor performance"""
    
    def process_request(self, request):
        """Start performance monitoring"""
        if hasattr(request, '_performance_monitor'):
            request._performance_monitor.start_timing()
    
    def process_response(self, request, response):
        """End performance monitoring"""
        if hasattr(request, '_performance_monitor'):
            request._performance_monitor.log_query_count()
            request._performance_monitor.end_timing(request, response)
        
        return response


# Initialize performance monitor for each request
class PerformanceMonitorInitMiddleware(MiddlewareMixin):
    """Initialize performance monitor for each request"""
    
    def process_request(self, request):
        """Initialize performance monitor"""
        request._performance_monitor = PerformanceMonitor()
        request._performance_monitor.start_timing()
