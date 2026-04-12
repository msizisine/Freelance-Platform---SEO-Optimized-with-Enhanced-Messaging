import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()

# Create superuser
user = None
if not User.objects.filter(email='admin@example.com').exists():
    user = User.objects.create_superuser(
        email='admin@example.com',
        password='admin123'
    )
    # Set additional fields after creation
    user.user_type = 'freelancer'
    user.save()
    print(f"Superuser created: {user.email}")
else:
    user = User.objects.get(email='admin@example.com')
    print("Superuser already exists")

# Create profile for the user
if user:
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        print("Profile created for superuser")
    else:
        print("Profile already exists for superuser")
