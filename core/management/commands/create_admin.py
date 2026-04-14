from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Run migrations and create superuser if it does not exist'

    def handle(self, *args, **options):
        # Run migrations first
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=1, interactive=False)
        
        # Create superuser
        User = get_user_model()
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
            self.stdout.write('Username: admin')
            self.stdout.write('Password: admin123')
            self.stdout.write('Access admin panel at: /admin/')
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))
