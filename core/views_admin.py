from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def create_superuser_view(request):
    """Temporary view to create superuser - REMOVE IN PRODUCTION"""
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Superuser created successfully',
            'username': 'admin',
            'password': 'admin123'
        })
    else:
        return JsonResponse({
            'status': 'info',
            'message': 'Superuser already exists'
        })
