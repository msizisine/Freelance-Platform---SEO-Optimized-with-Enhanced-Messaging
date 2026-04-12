import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from gigs.models import Category

# Create sample categories
categories_data = [
    {'name': 'Technology'},
    {'name': 'Design'},
    {'name': 'Writing'},
    {'name': 'Marketing'},
    {'name': 'Business'},
    {'name': 'Programming'},
    {'name': 'Data Entry'},
    {'name': 'Video Editing'},
    {'name': 'Translation'},
]

for cat_data in categories_data:
    category, created = Category.objects.get_or_create(name=cat_data['name'])
    if created:
        print(f"Created category: {category.name}")
    else:
        print(f"Category already exists: {category.name}")

print("Categories created successfully!")
