"""
Dynamic configuration model for flexible system settings
Designed to handle future changes without code modifications
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
import base64
from cryptography.fernet import Fernet
from django.conf import settings


class DynamicConfiguration(models.Model):
    """
    Dynamic configuration model that can handle any type of configuration
    Supports encrypted sensitive data and structured data types
    """
    
    CONFIG_CATEGORIES = [
        ('payment', 'Payment Settings'),
        ('banking', 'Banking Information'),
        ('whatsapp', 'WhatsApp Configuration'),
        ('email', 'Email Configuration'),
        ('sms', 'SMS Configuration'),
        ('platform', 'Platform Settings'),
        ('fees', 'Fee Structure'),
        ('api', 'API Keys & Credentials'),
        ('ui', 'User Interface'),
        ('notifications', 'Notification Settings'),
        ('security', 'Security Settings'),
        ('integrations', 'Third-party Integrations'),
    ]
    
    DATA_TYPES = [
        ('string', 'Text String'),
        ('integer', 'Integer Number'),
        ('decimal', 'Decimal Number'),
        ('boolean', 'True/False'),
        ('json', 'JSON Object'),
        ('list', 'List of Values'),
        ('encrypted', 'Encrypted Data'),
        ('url', 'URL Address'),
        ('email', 'Email Address'),
        ('phone', 'Phone Number'),
        ('file_path', 'File Path'),
        ('html', 'HTML Content'),
        ('css', 'CSS Styles'),
        ('javascript', 'JavaScript Code'),
    ]
    
    # Core fields
    key = models.CharField(max_length=100, unique=True, help_text="Unique configuration key")
    category = models.CharField(max_length=20, choices=CONFIG_CATEGORIES, help_text="Configuration category")
    data_type = models.CharField(max_length=20, choices=DATA_TYPES, default='string', help_text="Type of data stored")
    
    # Value storage
    value = models.TextField(help_text="Configuration value (encrypted for sensitive data)")
    encrypted_value = models.TextField(blank=True, null=True, help_text="Encrypted sensitive data")
    
    # Metadata
    name = models.CharField(max_length=200, help_text="Human-readable name")
    description = models.TextField(help_text="Detailed description of this configuration")
    
    # Validation and constraints
    is_required = models.BooleanField(default=False, help_text="Whether this configuration is required")
    validation_rules = models.JSONField(default=dict, blank=True, help_text="Validation rules as JSON")
    default_value = models.TextField(blank=True, help_text="Default value if not set")
    
    # Access control
    is_public = models.BooleanField(default=False, help_text="Whether this config is accessible to all users")
    is_editable = models.BooleanField(default=True, help_text="Whether this config can be edited")
    requires_restart = models.BooleanField(default=False, help_text="Whether app restart is needed after change")
    
    # Versioning and audit
    version = models.PositiveIntegerField(default=1, help_text="Configuration version")
    last_modified_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_configs')
    last_modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this configuration is active")
    
    class Meta:
        verbose_name = "Dynamic Configuration"
        verbose_name_plural = "Dynamic Configurations"
        ordering = ['category', 'key']
        indexes = [
            models.Index(fields=['category', 'key']),
            models.Index(fields=['is_active', 'category']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.name}"
    
    def clean(self):
        """Validate configuration based on data type and rules"""
        super().clean()
        
        if self.is_required and not self.get_value():
            raise ValidationError(f"Configuration '{self.key}' is required")
        
        # Validate based on data type
        value = self.get_value()
        if value is not None:
            if self.data_type == 'url' and not self._is_valid_url(value):
                raise ValidationError("Invalid URL format")
            elif self.data_type == 'email' and not self._is_valid_email(value):
                raise ValidationError("Invalid email format")
            elif self.data_type == 'phone' and not self._is_valid_phone(value):
                raise ValidationError("Invalid phone format")
            elif self.data_type in ['integer', 'decimal'] and not self._is_valid_number(value):
                raise ValidationError("Invalid number format")
        
        # Apply custom validation rules
        self._apply_validation_rules(value)
    
    def _is_valid_url(self, value):
        """Validate URL format"""
        from django.core.validators import URLValidator
        try:
            URLValidator()(value)
            return True
        except ValidationError:
            return False
    
    def _is_valid_email(self, value):
        """Validate email format"""
        from django.core.validators import EmailValidator
        try:
            EmailValidator()(value)
            return True
        except ValidationError:
            return False
    
    def _is_valid_phone(self, value):
        """Validate phone format"""
        import re
        # Basic phone validation - can be enhanced
        phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
        return re.match(phone_pattern, value.replace(' ', '').replace('-', '')) is not None
    
    def _is_valid_number(self, value):
        """Validate number format"""
        try:
            if self.data_type == 'integer':
                int(value)
            elif self.data_type == 'decimal':
                float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _apply_validation_rules(self, value):
        """Apply custom validation rules"""
        if not self.validation_rules:
            return
        
        rules = self.validation_rules
        
        # Min/max validation for numbers
        if 'min_value' in rules and self.data_type in ['integer', 'decimal']:
            if float(value) < float(rules['min_value']):
                raise ValidationError(f"Value must be at least {rules['min_value']}")
        
        if 'max_value' in rules and self.data_type in ['integer', 'decimal']:
            if float(value) > float(rules['max_value']):
                raise ValidationError(f"Value must be at most {rules['max_value']}")
        
        # Length validation for strings
        if 'min_length' in rules and self.data_type in ['string', 'url', 'email', 'phone']:
            if len(value) < int(rules['min_length']):
                raise ValidationError(f"Value must be at least {rules['min_length']} characters")
        
        if 'max_length' in rules and self.data_type in ['string', 'url', 'email', 'phone']:
            if len(value) > int(rules['max_length']):
                raise ValidationError(f"Value must be at most {rules['max_length']} characters")
        
        # Allowed values validation
        if 'allowed_values' in rules:
            allowed = rules['allowed_values']
            if value not in allowed:
                raise ValidationError(f"Value must be one of: {', '.join(allowed)}")
        
        # Pattern validation
        if 'pattern' in rules:
            import re
            pattern = rules['pattern']
            if not re.match(pattern, str(value)):
                raise ValidationError(f"Value does not match required pattern")
    
    def get_value(self):
        """Get the configuration value with proper type conversion"""
        if self.data_type == 'encrypted':
            return self._get_encrypted_value()
        else:
            return self._parse_value(self.value)
    
    def set_value(self, value):
        """Set the configuration value with proper type handling"""
        if self.data_type == 'encrypted':
            self._set_encrypted_value(value)
        else:
            self.value = self._serialize_value(value)
    
    def _parse_value(self, value):
        """Parse value based on data type"""
        if value is None or value == '':
            return None
        
        try:
            if self.data_type == 'integer':
                return int(value)
            elif self.data_type == 'decimal':
                return float(value)
            elif self.data_type == 'boolean':
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                return bool(value)
            elif self.data_type in ['json', 'list']:
                return json.loads(value)
            else:
                return value
        except (ValueError, json.JSONDecodeError):
            return value
    
    def _serialize_value(self, value):
        """Serialize value based on data type"""
        if value is None:
            return ''
        
        if self.data_type in ['json', 'list']:
            return json.dumps(value)
        else:
            return str(value)
    
    def _get_encrypted_value(self):
        """Get decrypted value"""
        if not self.encrypted_value:
            return None
        
        try:
            # Use encryption key from settings or generate one
            key = getattr(settings, 'CONFIG_ENCRYPTION_KEY', None)
            if not key:
                # Generate a key based on SECRET_KEY
                key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32].ljust(32, b'0'))
            
            f = Fernet(key)
            decrypted_value = f.decrypt(self.encrypted_value.encode()).decode()
            return self._parse_value(decrypted_value)
        except Exception:
            return None
    
    def _set_encrypted_value(self, value):
        """Set encrypted value"""
        try:
            # Use encryption key from settings or generate one
            key = getattr(settings, 'CONFIG_ENCRYPTION_KEY', None)
            if not key:
                # Generate a key based on SECRET_KEY
                key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32].ljust(32, b'0'))
            
            f = Fernet(key)
            serialized_value = self._serialize_value(value)
            self.encrypted_value = f.encrypt(serialized_value.encode()).decode()
            self.value = ''  # Clear unencrypted value
        except Exception as e:
            raise ValidationError(f"Failed to encrypt value: {str(e)}")
    
    def get_display_value(self):
        """Get a display-friendly value"""
        value = self.get_value()
        
        if value is None:
            return "Not set"
        
        if self.data_type == 'boolean':
            return "Yes" if value else "No"
        elif self.data_type == 'encrypted':
            return "****** (Encrypted)"
        elif self.data_type in ['json', 'list']:
            return json.dumps(value, indent=2) if value else "[]"
        else:
            return str(value)
    
    def reset_to_default(self):
        """Reset configuration to default value"""
        if self.default_value:
            self.set_value(self.default_value)
            self.save()
    
    @classmethod
    def get_config(cls, key, default=None):
        """Get configuration value by key"""
        try:
            config = cls.objects.get(key=key, is_active=True)
            value = config.get_value()
            return value if value is not None else default
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, key, value, user=None):
        """Set configuration value by key"""
        try:
            config = cls.objects.get(key=key)
            config.set_value(value)
            if user:
                config.last_modified_by = user
            config.save()
        except cls.DoesNotExist:
            raise ValueError(f"Configuration '{key}' not found")
    
    @classmethod
    def get_configs_by_category(cls, category):
        """Get all configurations in a category"""
        return cls.objects.filter(category=category, is_active=True)


class ConfigurationHistory(models.Model):
    """
    Track changes to dynamic configurations for audit purposes
    """
    configuration = models.ForeignKey(DynamicConfiguration, on_delete=models.CASCADE, related_name='history')
    old_value = models.TextField(blank=True, help_text="Previous value")
    new_value = models.TextField(blank=True, help_text="New value")
    changed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    change_reason = models.TextField(blank=True, help_text="Reason for the change")
    
    class Meta:
        verbose_name = "Configuration History"
        verbose_name_plural = "Configuration Histories"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['configuration', '-changed_at']),
            models.Index(fields=['changed_by', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.configuration.key} - {self.changed_at.strftime('%Y-%m-%d %H:%M')}"


class ConfigurationTemplate(models.Model):
    """
    Predefined configuration templates for easy setup
    """
    name = models.CharField(max_length=200, help_text="Template name")
    description = models.TextField(help_text="Template description")
    category = models.CharField(max_length=20, choices=DynamicConfiguration.CONFIG_CATEGORIES)
    configurations = models.JSONField(help_text="Template configurations as JSON")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Configuration Template"
        verbose_name_plural = "Configuration Templates"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def apply_template(self, user=None):
        """Apply this template to create configurations"""
        configs_created = 0
        for config_data in self.configurations:
            try:
                config, created = DynamicConfiguration.objects.get_or_create(
                    key=config_data['key'],
                    defaults={
                        **config_data,
                        'last_modified_by': user,
                    }
                )
                if created:
                    configs_created += 1
                elif config_data.get('overwrite', False):
                    for field, value in config_data.items():
                        if field != 'key':
                            setattr(config, field, value)
                    config.last_modified_by = user
                    config.save()
                    configs_created += 1
            except Exception as e:
                # Log error but continue with other configs
                pass
        
        return configs_created
