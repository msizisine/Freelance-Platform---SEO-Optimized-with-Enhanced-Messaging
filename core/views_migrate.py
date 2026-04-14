from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
def run_migrations(request):
    """Temporary view to run migrations - REMOVE IN PRODUCTION"""
    try:
        # Run migrations
        call_command('migrate', verbosity=0, interactive=False)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Migrations completed successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Migration failed: {str(e)}'
        })
