from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for admin access'

    def handle(self, *args, **options):
        email = 'admin@example.com'
        password = 'AdminPass123!@#'  # Stronger password that passes validators

        # Delete existing user completely
        User.objects.filter(email=email).delete()
        EmailAddress.objects.filter(email=email).delete()

        # Create user without password first
        user = User(
            email=email,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            user_type='homeowner'
        )

        # Set password explicitly (bypasses validators)
        user.set_password(password)

        # Save to database
        user.save()

        # Refresh from database
        user.refresh_from_db()

        # Verify password works
        password_works = user.check_password(password)

        # Create EmailAddress for allauth
        EmailAddress.objects.create(
            user=user,
            email=email,
            verified=True,
            primary=True
        )

        self.stdout.write(self.style.SUCCESS(f'✓ Superuser created: {email}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Password: {password}'))
        self.stdout.write(f'  is_active: {user.is_active}')
        self.stdout.write(f'  is_staff: {user.is_staff}')
        self.stdout.write(f'  is_superuser: {user.is_superuser}')
        self.stdout.write(f'  password_works: {password_works}')
        self.stdout.write(self.style.SUCCESS(f'✓ EmailAddress created and verified'))
