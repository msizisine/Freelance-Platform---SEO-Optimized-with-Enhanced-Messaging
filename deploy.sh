#!/bin/bash

# Production deployment script for Django freelance platform

set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build and start Docker containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for database to be ready
echo "Waiting for database..."
sleep 10

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser if needed
docker-compose exec web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Creating superuser...")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF

# Restart services
docker-compose restart web celery celery-beat

echo "Deployment completed successfully!"
echo "Your application is now running at http://your-domain.com"
echo "Admin access: http://your-domain.com/admin"
echo "Username: admin, Password: admin123 (change this in production!)"
