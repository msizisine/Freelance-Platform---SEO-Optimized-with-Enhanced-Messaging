# FreelanceHub - Django Freelance Platform

A comprehensive Django-based freelance marketplace platform similar to Fiverr, where freelancers can offer their services and clients can hire them for various projects.

## Features

### Core Functionality
- **User Authentication**: Email-based authentication with freelancer/client roles
- **Gig Management**: Create, edit, and manage service offerings with multiple pricing tiers
- **Order System**: Complete order lifecycle from placement to completion
- **Payment Processing**: Stripe integration for secure payments
- **Messaging System**: Real-time communication between users
- **Review System**: Rating and feedback system for completed orders
- **Search & Filtering**: Advanced search with category and price filters
- **User Profiles**: Comprehensive profiles with portfolios and skills

### Advanced Features
- **File Uploads**: Support for attachments in messages and deliveries
- **Notifications**: Real-time notifications for messages and orders
- **Dashboard**: Analytics and management interface
- **Admin Panel**: Full admin control over platform data
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5

## Tech Stack

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Django Allauth
- **Payments**: Stripe
- **Task Queue**: Celery with Redis
- **File Storage**: Django file system (can be extended to S3)

## Installation

### Prerequisites
- Python 3.8+
- Redis server (for Celery)
- Stripe account (for payments)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd freelance_platform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Start Redis server**
   ```bash
   redis-server
   ```

9. **Start Celery worker**
   ```bash
   celery -A freelance_platform worker -l info
   ```

10. **Run development server**
    ```bash
    python manage.py runserver
    ```

## Environment Variables

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Project Structure

```
freelance_platform/
├── freelance_platform/          # Main Django project
│   ├── __init__.py
│   ├── settings.py              # Django settings
│   ├── urls.py                  # Main URL configuration
│   ├── wsgi.py                  # WSGI configuration
│   ├── asgi.py                  # ASGI configuration
│   └── celery.py                # Celery configuration
├── core/                        # Core app (home, search)
├── users/                       # User management
├── gigs/                        # Gig/service management
├── orders/                      # Order processing
├── messages/                    # Messaging system
├── reviews/                     # Review and rating system
├── templates/                   # HTML templates
├── static/                      # Static files (CSS, JS, images)
├── media/                       # User uploaded files
├── requirements.txt             # Python dependencies
└── manage.py                    # Django management script
```

## App Details

### Core App
- Home page with featured gigs
- Search functionality
- Category browsing

### Users App
- User profiles with freelancer/client roles
- Portfolio management
- Skills and experience tracking
- Dashboard for analytics

### Gigs App
- Gig creation and management
- Multiple pricing packages (Basic, Standard, Premium)
- Category and subcategory organization
- Gig analytics and statistics

### Orders App
- Order lifecycle management
- Payment processing with Stripe
- File attachments and deliveries
- Order tracking and notifications

### Messages App
- Real-time messaging between users
- File attachments
- Message reporting and blocking
- Notification system

### Reviews App
- 5-star rating system
- Detailed feedback criteria
- Review responses
- Freelancer statistics

## Usage

### For Clients
1. Browse gigs by category or search for specific services
2. View gig details and freelancer profiles
3. Select a package and place an order
4. Communicate with the freelancer through the messaging system
5. Review delivered work and provide feedback

### For Freelancers
1. Create detailed gig profiles with multiple pricing tiers
2. Manage orders and communicate with clients
3. Deliver completed work through the platform
4. Build reputation through reviews and ratings
5. Track earnings and analytics

## Admin Features

The Django admin panel provides comprehensive control over:
- User management and verification
- Gig approval and moderation
- Order monitoring and dispute resolution
- Review management
- Platform analytics

## Deployment

### Production Setup

1. **Database**: Switch from SQLite to PostgreSQL
2. **Static Files**: Configure S3 or similar for static file serving
3. **Environment Variables**: Set production values
4. **Security**: Configure HTTPS, CSRF, and security settings
5. **Web Server**: Use Gunicorn with Nginx
6. **Process Management**: Use Supervisor for Celery workers

### Docker Deployment

A Docker setup can be created with:
- Dockerfile for the Django application
- docker-compose.yml for multi-service setup
- Redis and PostgreSQL containers
- Nginx reverse proxy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation for common issues

## Future Enhancements

- Real-time notifications with WebSockets
- Mobile app development
- Advanced analytics dashboard
- Multi-language support
- Escrow system for payments
- API for third-party integrations
- Subscription plans for premium features
