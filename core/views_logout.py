from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
@login_required
def custom_logout(request):
    """
    Custom logout view that ensures complete session cleanup
    """
    # Clear all session data
    if hasattr(request, 'session'):
        request.session.flush()
    
    # Perform Django logout
    logout(request)
    
    # Clear any remaining cookies
    response = redirect('/')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    
    # Add success message
    messages.success(request, 'You have been successfully logged out.')
    
    return response
