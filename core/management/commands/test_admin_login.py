from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Test admin login credentials'

    def handle(self, *args, **options):
        email = 'admin@example.com'
        password = 'admin123'
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f'User found: {email}')
            self.stdout.write(f'is_active: {user.is_active}')
            self.stdout.write(f'is_staff: {user.is_staff}')
            self.stdout.write(f'is_superuser: {user.is_superuser}')
            self.stdout.write(f'Password hash: {user.password}')
            
            # Test password
            if user.check_password(password):
                self.stdout.write(self.style.SUCCESS(f'✓ Password "{password}" is CORRECT'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Password "{password}" is INCORRECT'))
                self.stdout.write('Resetting password...')
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS('Password reset and saved'))
                
                # Verify again
                user.refresh_from_db()
                if user.check_password(password):
                    self.stdout.write(self.style.SUCCESS(f'✓ Password now works'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Password still does not work'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {email} does not exist'))
