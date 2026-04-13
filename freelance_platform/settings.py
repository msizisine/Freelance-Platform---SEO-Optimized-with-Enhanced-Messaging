import os
import sys
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Add project root to Python path for importing modules like phone_utils
sys.path.insert(0, str(BASE_DIR))

# Railway deployment rebuild - 2026-04-12

SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    # 'taggit',  # Temporarily disabled due to Django compatibility issues
    # 'django_filters',  # Temporarily disabled due to compatibility issues
    # 'debug_toolbar',   # Temporarily disabled
]

LOCAL_APPS = [
    'users',
    'gigs',
    'orders',
    'messaging',  # Renamed from 'messages' to avoid conflicts
    'reviews',
    'core',
    'notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # Temporarily disabled
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'freelance_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.unread_messages_count',
                'core.context_processors.user_profile_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'freelance_platform.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disabled for development
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300

# Logout settings
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SESSION_COOKIE_AGE = 3600  # 1 hour
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False

LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='pk_test_your-stripe-publishable-key')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='sk_test_your-stripe-secret-key')

CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

INTERNAL_IPS = ['127.0.0.1']

# CSRF Settings
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='https://pro4me.up.railway.app,http://localhost:8000,http://127.0.0.1:8000', cast=lambda v: [s.strip() for s in v.split(',')])

# Communication Settings
SITE_URL = config('SITE_URL', default='http://localhost:8000')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@freelanceplatform.com')

# WhatsApp Configuration
WHATSAPP_PROVIDER = os.environ.get('WHATSAPP_PROVIDER', 'wasender')
WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY', '')
WHATSAPP_PHONE_NUMBER = os.environ.get('WHATSAPP_PHONE_NUMBER', '')
WHATSAPP_WEBHOOK_URL = os.environ.get('WHATSAPP_WEBHOOK_URL', '')

# WasenderAPI Configuration
WASENDER_API_KEY = config('WASENDER_API_KEY', default='47fc123654d8cdda18a6311e71a6de8e48757438396255af45be40f1ef3c6f56')
WASENDER_WEBHOOK_SECRET = os.environ.get('WASENDER_WEBHOOK_SECRET', '')

# 360Dialog Configuration
WHATSAPP_DIALOG360_API_KEY = os.environ.get('WHATSAPP_DIALOG360_API_KEY', '')
WHATSAPP_DIALOG360_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_DIALOG360_PHONE_NUMBER_ID', '')

# Meta Direct WhatsApp Configuration
WHATSAPP_META_ACCESS_TOKEN = os.environ.get('WHATSAPP_META_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_WEBHOOK_VERIFICATION_TOKEN = os.environ.get('WHATSAPP_WEBHOOK_VERIFICATION_TOKEN', '')

# Twilio Configuration (Legacy)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
TWILIO_WHATSAPP_ENABLED = config('TWILIO_WHATSAPP_ENABLED', default=False, cast=bool)

# SMS Configuration
SMS_ENABLED = config('SMS_ENABLED', default=True, cast=bool)
SMS_FALLBACK_ENABLED = config('SMS_FALLBACK_ENABLED', default=True, cast=bool)
SMS_PROVIDER = config('SMS_PROVIDER', default='twilio')  # twilio, aws_sns, etc.

# Twilio SMS Configuration
TWILIO_SMS_ACCOUNT_SID = config('TWILIO_SMS_ACCOUNT_SID', default=TWILIO_ACCOUNT_SID)
TWILIO_SMS_AUTH_TOKEN = config('TWILIO_SMS_AUTH_TOKEN', default=TWILIO_AUTH_TOKEN)
TWILIO_SMS_PHONE_NUMBER = config('TWILIO_SMS_PHONE_NUMBER', default=TWILIO_PHONE_NUMBER)

# Email Settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='mavundlamsizi@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='occlhlaqnqmldoaq')
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=30, cast=int)

# Additional email settings
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='mavundlamsizi@gmail.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='mavundlamsizi@gmail.com')

# Email settings for development/production
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Ozow Payment Gateway Configuration
OZOW_SITE_ID = config('OZOW_SITE_ID', default='SPH-PRO-001')
OZOW_API_KEY = config('OZOW_API_KEY', default='c7286afbbee74924bdd6bb4c03f3b0f4')
OZOW_PRIVATE_KEY = config('OZOW_PRIVATE_KEY', default='8c005573fc4c4bb4b9d16806010ef012')
OZOW_API_SECRET = config('OZOW_API_SECRET', default='8c005573fc4c4bb4b9d16806010ef012')

if DEBUG:
    try:
        import debug_toolbar
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda x: True,
        }
    except ImportError:
        DEBUG_TOOLBAR_CONFIG = {}
