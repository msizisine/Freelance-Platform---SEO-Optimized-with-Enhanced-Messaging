from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for admin access'

    def handle(self, *args, **options):
        email = 'admin@example.com'
        password = 'admin123'

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser created: {email}'))
        else:
            # Ensure existing user has correct permissions
            if not user.is_active or not user.is_staff or not user.is_superuser:
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Superuser updated: {email}'))
            else:
                self.stdout.write(self.style.WARNING(f'Superuser already exists: {email}'))

        # Verify the user
        user.refresh_from_db()
        self.stdout.write(f'User status - is_active: {user.is_active}, is_staff: {user.is_staff}, is_superuser: {user.is_superuser}')
