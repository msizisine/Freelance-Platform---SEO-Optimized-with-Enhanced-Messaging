from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for admin access'

    def handle(self, *args, **options):
        email = 'admin@example.com'
        password = 'admin123'

        # Delete existing user if it exists to ensure clean state
        User.objects.filter(email=email).delete()

        # Create fresh superuser using the manager's create_superuser method
        user = User.objects.create_superuser(
            email=email,
            password=password
        )

        self.stdout.write(self.style.SUCCESS(f'Superuser created: {email}'))
        self.stdout.write(f'User status - is_active: {user.is_active}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}')
