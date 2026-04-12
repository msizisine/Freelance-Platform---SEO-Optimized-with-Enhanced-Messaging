"""
Initialize system configurations for the platform
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models_config import (
    SystemConfiguration, BankAccount, PaymentMethod, 
    PlatformFee, EmailConfiguration
)
import json


class Command(BaseCommand):
    help = 'Initialize system configurations for the platform'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing system configurations...')
        
        # Initialize payment methods
        self.init_payment_methods()
        
        # Initialize platform fees
        self.init_platform_fees()
        
        # Initialize system configurations
        self.init_system_configurations()
        
        # Initialize email configuration
        self.init_email_configuration()
        
        self.stdout.write(self.style.SUCCESS('System configurations initialized successfully!'))
    
    def init_payment_methods(self):
        """Initialize default payment methods"""
        default_methods = [
            {
                'method_type': 'yoco',
                'name': 'Yoco Mobile Payment',
                'description': 'Accept card payments using Yoco mobile payment system',
                'icon_class': 'fas fa-mobile-alt',
                'fee_percentage': 2.90,
                'fee_fixed': 0.00,
                'minimum_amount': 10.00,
                'processing_time': 'Instant',
                'instructions': 'Service provider will process your card payment using Yoco mobile device.',
                'sort_order': 1
            },
            {
                'method_type': 'ozow',
                'name': 'Ozow Instant EFT',
                'description': 'Instant EFT from all major South African banks',
                'icon_class': 'fas fa-bolt',
                'fee_percentage': 1.50,
                'fee_fixed': 0.00,
                'minimum_amount': 50.00,
                'processing_time': 'Instant',
                'instructions': 'Select your bank and complete payment using your online banking credentials.',
                'sort_order': 2
            },
            {
                'method_type': 'eft',
                'name': 'EFT Transfer',
                'description': 'Direct bank transfer to our business account',
                'icon_class': 'fas fa-university',
                'fee_percentage': 0.00,
                'fee_fixed': 0.00,
                'minimum_amount': 100.00,
                'processing_time': '1-2 business days',
                'instructions': 'Transfer the amount to our bank account using your order number as reference.',
                'sort_order': 3
            },
            {
                'method_type': 'in_person',
                'name': 'In-Person Payment',
                'description': 'Pay directly when work is completed',
                'icon_class': 'fas fa-handshake',
                'fee_percentage': 0.00,
                'fee_fixed': 0.00,
                'minimum_amount': 0.00,
                'processing_time': 'Immediate',
                'instructions': 'Pay the service provider directly when the work is completed to your satisfaction.',
                'sort_order': 4
            }
        ]
        
        for method_data in default_methods:
            method, created = PaymentMethod.objects.get_or_create(
                method_type=method_data['method_type'],
                defaults=method_data
            )
            if created:
                self.stdout.write(f'Created payment method: {method.name}')
            else:
                self.stdout.write(f'Payment method already exists: {method.name}')
    
    def init_platform_fees(self):
        """Initialize default platform fees"""
        default_fees = [
            {
                'fee_type': 'commission',
                'name': 'Service Commission',
                'description': 'Commission charged to service providers for completed jobs',
                'fee_percentage': 10.00,
                'fee_fixed': 0.00,
                'applies_to': 'service_provider',
                'minimum_amount': 0.00
            },
            {
                'fee_type': 'service_fee',
                'name': 'Platform Service Fee',
                'description': 'Service fee for using the platform',
                'fee_percentage': 0.00,
                'fee_fixed': 5.00,
                'applies_to': 'homeowner',
                'minimum_amount': 0.00
            },
            {
                'fee_type': 'transaction_fee',
                'name': 'Payment Processing Fee',
                'description': 'Fee for processing payments through payment gateways',
                'fee_percentage': 0.00,
                'fee_fixed': 0.00,
                'applies_to': 'both',
                'minimum_amount': 0.00
            }
        ]
        
        for fee_data in default_fees:
            fee, created = PlatformFee.objects.get_or_create(
                fee_type=fee_data['fee_type'],
                defaults=fee_data
            )
            if created:
                self.stdout.write(f'Created platform fee: {fee.name}')
            else:
                self.stdout.write(f'Platform fee already exists: {fee.name}')
    
    def init_system_configurations(self):
        """Initialize default system configurations"""
        default_configs = [
            {
                'key': 'platform_name',
                'value': 'Home Services Hub',
                'config_type': 'platform',
                'description': 'Name of the platform'
            },
            {
                'key': 'platform_email',
                'value': 'info@homeserviceshub.co.za',
                'config_type': 'platform',
                'description': 'Platform contact email'
            },
            {
                'key': 'platform_phone',
                'value': '+27 12 345 6789',
                'config_type': 'platform',
                'description': 'Platform contact phone'
            },
            {
                'key': 'commission_rate',
                'value': 10.0,
                'config_type': 'fees',
                'description': 'Default commission rate for service providers'
            },
            {
                'key': 'minimum_payout',
                'value': 100.0,
                'config_type': 'fees',
                'description': 'Minimum amount for service provider payouts'
            },
            {
                'key': 'whatsapp_enabled',
                'value': True,
                'config_type': 'whatsapp',
                'description': 'Enable WhatsApp notifications'
            },
            {
                'key': 'whatsapp_phone',
                'value': '+27 12 345 6789',
                'config_type': 'whatsapp',
                'description': 'WhatsApp business phone number'
            },
            {
                'key': 'auto_approve_reviews',
                'value': False,
                'config_type': 'platform',
                'description': 'Auto-approve reviews without moderation'
            }
        ]
        
        for config_data in default_configs:
            config, created = SystemConfiguration.objects.get_or_create(
                key=config_data['key'],
                defaults=config_data
            )
            if created:
                self.stdout.write(f'Created system config: {config.key}')
            else:
                self.stdout.write(f'System config already exists: {config.key}')
    
    def init_email_configuration(self):
        """Initialize default email configuration"""
        # Check if email config already exists
        existing_config = EmailConfiguration.objects.filter(is_active=True).first()
        if existing_config:
            self.stdout.write('Email configuration already exists')
            return
        
        # Create default email configuration using current .env settings
        from django.conf import settings
        
        email_config = EmailConfiguration.objects.create(
            config_type='smtp',
            is_active=True,
            host=getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'),
            port=getattr(settings, 'EMAIL_PORT', 587),
            username=getattr(settings, 'EMAIL_HOST_USER', ''),
            password=getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            use_tls=getattr(settings, 'EMAIL_USE_TLS', True),
            use_ssl=getattr(settings, 'EMAIL_USE_SSL', False),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@homeserviceshub.co.za'),
            from_name='Home Services Hub',
            daily_limit=1000
        )
        
        self.stdout.write(f'Created email configuration: {email_config.get_config_type_display()}')
