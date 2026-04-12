import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from gigs.models import Category

# Create home service categories
service_categories = [
    {'name': 'Plumbing'},
    {'name': 'Building'},
    {'name': 'Electrical'},
    {'name': 'Cleaning'},
    {'name': 'Painting'},
    {'name': 'Gardening'},
    {'name': 'General Work'},
]

# Clear existing categories
Category.objects.all().delete()

# Create new service categories
for cat_data in service_categories:
    category, created = Category.objects.get_or_create(name=cat_data['name'])
    if created:
        print(f"Created category: {category.name}")
    else:
        print(f"Category already exists: {category.name}")

print("Service categories created successfully!")
