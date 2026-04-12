"""
Initialize dynamic configurations for the platform
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models_dynamic_config import DynamicConfiguration, ConfigurationTemplate
import json


class Command(BaseCommand):
    help = 'Initialize dynamic configurations for the platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing configurations'
        )
        parser.add_argument(
            '--template',
            type=str,
            help='Apply specific template by name'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing dynamic configurations...')
        
        overwrite = options.get('overwrite', False)
        template_name = options.get('template')
        
        if template_name:
            # Apply specific template
            self.apply_template(template_name)
        else:
            # Initialize all default configurations
            self.init_platform_configs(overwrite)
            self.init_payment_configs(overwrite)
            self.init_banking_configs(overwrite)
            self.init_whatsapp_configs(overwrite)
            self.init_email_configs(overwrite)
            self.init_fee_configs(overwrite)
            self.init_api_configs(overwrite)
            self.init_ui_configs(overwrite)
            self.init_security_configs(overwrite)
        
        self.stdout.write(self.style.SUCCESS('Dynamic configurations initialized successfully!'))
    
    def init_platform_configs(self, overwrite=False):
        """Initialize platform configurations"""
        self.stdout.write('Initializing platform configurations...')
        
        configs = [
            {
                'key': 'platform_name',
                'name': 'Platform Name',
                'category': 'platform',
                'data_type': 'string',
                'value': 'Home Services Hub',
                'description': 'Name of the platform',
                'is_public': True,
                'validation_rules': {'min_length': 2, 'max_length': 100}
            },
            {
                'key': 'platform_email',
                'name': 'Platform Email',
                'category': 'platform',
                'data_type': 'email',
                'value': 'info@homeserviceshub.co.za',
                'description': 'Platform contact email address',
                'is_public': True,
                'validation_rules': {'required': True}
            },
            {
                'key': 'platform_phone',
                'name': 'Platform Phone',
                'category': 'platform',
                'data_type': 'phone',
                'value': '+27 12 345 6789',
                'description': 'Platform contact phone number',
                'is_public': True,
                'validation_rules': {'pattern': r'^\+\d{1,3}\s?\d{3,14}$'}
            },
            {
                'key': 'platform_website',
                'name': 'Platform Website',
                'category': 'platform',
                'data_type': 'url',
                'value': 'https://homeserviceshub.co.za',
                'description': 'Platform website URL',
                'is_public': True
            },
            {
                'key': 'platform_address',
                'name': 'Platform Address',
                'category': 'platform',
                'data_type': 'string',
                'value': '123 Main St, Johannesburg, South Africa',
                'description': 'Platform physical address',
                'is_public': True
            },
            {
                'key': 'auto_approve_reviews',
                'name': 'Auto-approve Reviews',
                'category': 'platform',
                'data_type': 'boolean',
                'value': False,
                'description': 'Automatically approve reviews without moderation',
                'is_public': False
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_payment_configs(self, overwrite=False):
        """Initialize payment configurations"""
        self.stdout.write('Initializing payment configurations...')
        
        configs = [
            {
                'key': 'payment_methods_enabled',
                'name': 'Enabled Payment Methods',
                'category': 'payment',
                'data_type': 'list',
                'value': ['yoco', 'ozow', 'eft', 'in_person'],
                'description': 'List of enabled payment methods',
                'is_public': False,
                'validation_rules': {'allowed_values': ['yoco', 'ozow', 'eft', 'in_person', 'payfast']}
            },
            {
                'key': 'default_payment_method',
                'name': 'Default Payment Method',
                'category': 'payment',
                'data_type': 'string',
                'value': 'eft',
                'description': 'Default payment method selection',
                'is_public': False,
                'validation_rules': {'allowed_values': ['yoco', 'ozow', 'eft', 'in_person', 'payfast']}
            },
            {
                'key': 'payment_timeout_minutes',
                'name': 'Payment Timeout',
                'category': 'payment',
                'data_type': 'integer',
                'value': 30,
                'description': 'Payment session timeout in minutes',
                'is_public': False,
                'validation_rules': {'min_value': 5, 'max_value': 120}
            },
            {
                'key': 'auto_confirm_payments',
                'name': 'Auto-confirm Payments',
                'category': 'payment',
                'data_type': 'boolean',
                'value': False,
                'description': 'Automatically confirm payments without manual verification',
                'is_public': False
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_banking_configs(self, overwrite=False):
        """Initialize banking configurations"""
        self.stdout.write('Initializing banking configurations...')
        
        configs = [
            {
                'key': 'default_bank_account_id',
                'name': 'Default Bank Account ID',
                'category': 'banking',
                'data_type': 'integer',
                'value': None,
                'description': 'ID of the default bank account for EFT payments',
                'is_public': False,
                'is_required': False
            },
            {
                'key': 'eft_verification_hours',
                'name': 'EFT Verification Time',
                'category': 'banking',
                'data_type': 'integer',
                'value': 48,
                'description': 'Hours to verify EFT payments',
                'is_public': False,
                'validation_rules': {'min_value': 1, 'max_value': 168}
            },
            {
                'key': 'bank_transfer_reference_prefix',
                'name': 'Bank Reference Prefix',
                'category': 'banking',
                'data_type': 'string',
                'value': 'HSH',
                'description': 'Prefix for bank transfer references',
                'is_public': False,
                'validation_rules': {'max_length': 10}
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_whatsapp_configs(self, overwrite=False):
        """Initialize WhatsApp configurations"""
        self.stdout.write('Initializing WhatsApp configurations...')
        
        configs = [
            {
                'key': 'whatsapp_enabled',
                'name': 'WhatsApp Enabled',
                'category': 'whatsapp',
                'data_type': 'boolean',
                'value': True,
                'description': 'Enable WhatsApp notifications',
                'is_public': False
            },
            {
                'key': 'whatsapp_phone',
                'name': 'WhatsApp Phone Number',
                'category': 'whatsapp',
                'data_type': 'phone',
                'value': '+27 12 345 6789',
                'description': 'WhatsApp business phone number',
                'is_public': False,
                'validation_rules': {'pattern': r'^\+\d{1,3}\s?\d{3,14}$'}
            },
            {
                'key': 'whatsapp_api_key',
                'name': 'WhatsApp API Key',
                'category': 'whatsapp',
                'data_type': 'encrypted',
                'value': '',
                'description': 'WhatsApp API key (encrypted)',
                'is_public': False,
                'is_required': False
            },
            {
                'key': 'whatsapp_webhook_url',
                'name': 'WhatsApp Webhook URL',
                'category': 'whatsapp',
                'data_type': 'url',
                'value': 'https://homeserviceshub.co.za/whatsapp/webhook/',
                'description': 'WhatsApp webhook URL',
                'is_public': False
            },
            {
                'key': 'whatsapp_template_namespace',
                'name': 'WhatsApp Template Namespace',
                'category': 'whatsapp',
                'data_type': 'string',
                'value': 'homeserviceshub',
                'description': 'WhatsApp message template namespace',
                'is_public': False
            },
            {
                'key': 'whatsapp_rate_limit',
                'name': 'WhatsApp Rate Limit',
                'category': 'whatsapp',
                'data_type': 'integer',
                'value': 10,
                'description': 'Messages per minute rate limit',
                'is_public': False,
                'validation_rules': {'min_value': 1, 'max_value': 100}
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_email_configs(self, overwrite=False):
        """Initialize email configurations"""
        self.stdout.write('Initializing email configurations...')
        
        configs = [
            {
                'key': 'smtp_host',
                'name': 'SMTP Host',
                'category': 'email',
                'data_type': 'string',
                'value': 'smtp.gmail.com',
                'description': 'SMTP server host',
                'is_public': False,
                'validation_rules': {'required': True}
            },
            {
                'key': 'smtp_port',
                'name': 'SMTP Port',
                'category': 'email',
                'data_type': 'integer',
                'value': 587,
                'description': 'SMTP server port',
                'is_public': False,
                'validation_rules': {'min_value': 1, 'max_value': 65535}
            },
            {
                'key': 'smtp_username',
                'name': 'SMTP Username',
                'category': 'email',
                'data_type': 'email',
                'value': 'info@homeserviceshub.co.za',
                'description': 'SMTP username',
                'is_public': False
            },
            {
                'key': 'smtp_password',
                'name': 'SMTP Password',
                'category': 'email',
                'data_type': 'encrypted',
                'value': '',
                'description': 'SMTP password (encrypted)',
                'is_public': False,
                'is_required': False
            },
            {
                'key': 'smtp_use_tls',
                'name': 'Use TLS',
                'category': 'email',
                'data_type': 'boolean',
                'value': True,
                'description': 'Use TLS encryption for SMTP',
                'is_public': False
            },
            {
                'key': 'smtp_use_ssl',
                'name': 'Use SSL',
                'category': 'email',
                'data_type': 'boolean',
                'value': False,
                'description': 'Use SSL encryption for SMTP',
                'is_public': False
            },
            {
                'key': 'email_from',
                'name': 'Default From Email',
                'category': 'email',
                'data_type': 'email',
                'value': 'info@homeserviceshub.co.za',
                'description': 'Default from email address',
                'is_public': False,
                'validation_rules': {'required': True}
            },
            {
                'key': 'email_from_name',
                'name': 'Default From Name',
                'category': 'email',
                'data_type': 'string',
                'value': 'Home Services Hub',
                'description': 'Default from name',
                'is_public': False,
                'validation_rules': {'min_length': 2, 'max_length': 100}
            },
            {
                'key': 'email_daily_limit',
                'name': 'Email Daily Limit',
                'category': 'email',
                'data_type': 'integer',
                'value': 1000,
                'description': 'Daily email sending limit',
                'is_public': False,
                'validation_rules': {'min_value': 10, 'max_value': 10000}
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_fee_configs(self, overwrite=False):
        """Initialize fee configurations"""
        self.stdout.write('Initializing fee configurations...')
        
        configs = [
            {
                'key': 'commission_rate',
                'name': 'Commission Rate',
                'category': 'fees',
                'data_type': 'decimal',
                'value': 10.0,
                'description': 'Service provider commission rate (percentage)',
                'is_public': False,
                'validation_rules': {'min_value': 0, 'max_value': 50}
            },
            {
                'key': 'service_fee',
                'name': 'Service Fee',
                'category': 'fees',
                'data_type': 'decimal',
                'value': 5.0,
                'description': 'Platform service fee (fixed amount)',
                'is_public': False,
                'validation_rules': {'min_value': 0, 'max_value': 100}
            },
            {
                'key': 'minimum_payout',
                'name': 'Minimum Payout',
                'category': 'fees',
                'data_type': 'decimal',
                'value': 100.0,
                'description': 'Minimum amount for service provider payouts',
                'is_public': False,
                'validation_rules': {'min_value': 10, 'max_value': 10000}
            },
            {
                'key': 'payment_processing_fee',
                'name': 'Payment Processing Fee',
                'category': 'fees',
                'data_type': 'decimal',
                'value': 2.9,
                'description': 'Payment processing fee percentage',
                'is_public': False,
                'validation_rules': {'min_value': 0, 'max_value': 10}
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_api_configs(self, overwrite=False):
        """Initialize API configurations"""
        self.stdout.write('Initializing API configurations...')
        
        configs = [
            {
                'key': 'ozow_site_id',
                'name': 'Ozow Site ID',
                'category': 'api',
                'data_type': 'string',
                'value': 'SPH-PRO-001',
                'description': 'Ozow payment site ID',
                'is_public': False
            },
            {
                'key': 'ozow_api_key',
                'name': 'Ozow API Key',
                'category': 'api',
                'data_type': 'encrypted',
                'value': '',
                'description': 'Ozow API key (encrypted)',
                'is_public': False,
                'is_required': False
            },
            {
                'key': 'ozow_api_secret',
                'name': 'Ozow API Secret',
                'category': 'api',
                'data_type': 'encrypted',
                'value': '',
                'description': 'Ozow API secret (encrypted)',
                'is_public': False,
                'is_required': False
            },
            {
                'key': 'google_maps_api_key',
                'name': 'Google Maps API Key',
                'category': 'api',
                'data_type': 'encrypted',
                'value': '',
                'description': 'Google Maps API key (encrypted)',
                'is_public': False,
                'is_required': False
            },
            {
                'key': 'recaptcha_site_key',
                'name': 'reCAPTCHA Site Key',
                'category': 'api',
                'data_type': 'string',
                'value': '',
                'description': 'Google reCAPTCHA site key',
                'is_public': True,
                'is_required': False
            },
            {
                'key': 'recaptcha_secret_key',
                'name': 'reCAPTCHA Secret Key',
                'category': 'api',
                'data_type': 'encrypted',
                'value': '',
                'description': 'Google reCAPTCHA secret key (encrypted)',
                'is_public': False,
                'is_required': False
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_ui_configs(self, overwrite=False):
        """Initialize UI configurations"""
        self.stdout.write('Initializing UI configurations...')
        
        configs = [
            {
                'key': 'site_logo_url',
                'name': 'Site Logo URL',
                'category': 'ui',
                'data_type': 'url',
                'value': '/static/images/logo.png',
                'description': 'URL of the site logo',
                'is_public': True
            },
            {
                'key': 'site_favicon_url',
                'name': 'Site Favicon URL',
                'category': 'ui',
                'data_type': 'url',
                'value': '/static/images/favicon.ico',
                'description': 'URL of the site favicon',
                'is_public': True
            },
            {
                'key': 'primary_color',
                'name': 'Primary Color',
                'category': 'ui',
                'data_type': 'string',
                'value': '#007bff',
                'description': 'Primary theme color',
                'is_public': True,
                'validation_rules': {'pattern': r'^#[0-9a-fA-F]{6}$'}
            },
            {
                'key': 'secondary_color',
                'name': 'Secondary Color',
                'category': 'ui',
                'data_type': 'string',
                'value': '#6c757d',
                'description': 'Secondary theme color',
                'is_public': True,
                'validation_rules': {'pattern': r'^#[0-9a-fA-F]{6}$'}
            },
            {
                'key': 'site_theme',
                'name': 'Site Theme',
                'category': 'ui',
                'data_type': 'string',
                'value': 'bootstrap',
                'description': 'Site theme framework',
                'is_public': False,
                'validation_rules': {'allowed_values': ['bootstrap', 'tailwind', 'custom']}
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def init_security_configs(self, overwrite=False):
        """Initialize security configurations"""
        self.stdout.write('Initializing security configurations...')
        
        configs = [
            {
                'key': 'session_timeout_minutes',
                'name': 'Session Timeout',
                'category': 'security',
                'data_type': 'integer',
                'value': 120,
                'description': 'User session timeout in minutes',
                'is_public': False,
                'validation_rules': {'min_value': 5, 'max_value': 1440}
            },
            {
                'key': 'max_login_attempts',
                'name': 'Max Login Attempts',
                'category': 'security',
                'data_type': 'integer',
                'value': 5,
                'description': 'Maximum login attempts before lockout',
                'is_public': False,
                'validation_rules': {'min_value': 3, 'max_value': 20}
            },
            {
                'key': 'lockout_duration_minutes',
                'name': 'Lockout Duration',
                'category': 'security',
                'data_type': 'integer',
                'value': 30,
                'description': 'Account lockout duration in minutes',
                'is_public': False,
                'validation_rules': {'min_value': 5, 'max_value': 1440}
            },
            {
                'key': 'require_email_verification',
                'name': 'Require Email Verification',
                'category': 'security',
                'data_type': 'boolean',
                'value': True,
                'description': 'Require email verification for new accounts',
                'is_public': False
            },
            {
                'key': 'enable_two_factor_auth',
                'name': 'Enable Two-Factor Auth',
                'category': 'security',
                'data_type': 'boolean',
                'value': False,
                'description': 'Enable two-factor authentication',
                'is_public': False
            }
        ]
        
        self.create_configs(configs, overwrite)
    
    def create_configs(self, configs, overwrite=False):
        """Create configurations from list"""
        created_count = 0
        updated_count = 0
        
        for config_data in configs:
            try:
                config, created = DynamicConfiguration.objects.get_or_create(
                    key=config_data['key'],
                    defaults=config_data
                )
                
                if created:
                    self.stdout.write(f"  Created: {config.key}")
                    created_count += 1
                elif overwrite:
                    # Update existing config
                    for field, value in config_data.items():
                        if field != 'key':
                            setattr(config, field, value)
                    config.save()
                    self.stdout.write(f"  Updated: {config.key}")
                    updated_count += 1
                else:
                    self.stdout.write(f"  Exists: {config.key}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error creating {config_data['key']}: {str(e)}")
                )
        
        if created_count > 0:
            self.stdout.write(f"  Created {created_count} configurations")
        if updated_count > 0:
            self.stdout.write(f"  Updated {updated_count} configurations")
    
    def apply_template(self, template_name):
        """Apply a specific configuration template"""
        self.stdout.write(f'Applying template: {template_name}')
        
        try:
            template = ConfigurationTemplate.objects.get(name=template_name, is_active=True)
            created = template.apply_template()
            self.stdout.write(f'  Applied template - created {created} configurations')
        except ConfigurationTemplate.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Template "{template_name}" not found')
            )
