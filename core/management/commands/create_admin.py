from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from allauth.account.models import EmailAddress

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for admin access'

    def handle(self, *args, **options):
        # Run migrations first
        self.stdout.write('Running migrations...')
        call_command('migrate', verbosity=1, interactive=False)
        
        email = 'admin@example.com'
        password = 'AdminPass123!@#'

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

        # Set password explicitly
        user.set_password(password)
        self.stdout.write(f'After set_password: {user.password[:50]}...')

        # Save to database
        user.save()
        self.stdout.write(f'After save: {user.password[:50]}...')

        # Query database directly to verify
        with connection.cursor() as cursor:
            cursor.execute('SELECT password FROM core_user WHERE email = %s', [email])
            row = cursor.fetchone()
            if row:
                db_password = row[0]
                self.stdout.write(f'Database password: {db_password[:50]}...')
            else:
                self.stdout.write(self.style.ERROR('User not found in database!'))

        # Refresh from database
        user.refresh_from_db()
        self.stdout.write(f'After refresh: {user.password[:50]}...')

        # Test password multiple times
        test1 = user.check_password(password)
        test2 = user.check_password(password)
        self.stdout.write(f'check_password test 1: {test1}')
        self.stdout.write(f'check_password test 2: {test2}')

        # If password doesn't work, try again
        if not test1:
            self.stdout.write(self.style.WARNING('Password check failed! Trying again...'))
            user.set_password(password)
            user.save()
            user.refresh_from_db()
            test3 = user.check_password(password)
            self.stdout.write(f'check_password test 3 (after retry): {test3}')

        # Create EmailAddress for allauth
        EmailAddress.objects.create(
            user=user,
            email=email,
            verified=True,
            primary=True
        )

        self.stdout.write(self.style.SUCCESS(f'Superuser created: {email}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(f'  is_active: {user.is_active}')
        self.stdout.write(f'  is_staff: {user.is_staff}')
        self.stdout.write(f'  is_superuser: {user.is_superuser}')
        self.stdout.write(self.style.SUCCESS(f'EmailAddress created and verified'))
