from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Import models and signals when app is ready"""
        # Import dynamic configuration models
        from .models_dynamic_config import (
            DynamicConfiguration, ConfigurationHistory, ConfigurationTemplate
        )
        # Import configuration models
        from .models_config import (
            SystemConfiguration, BankAccount, PaymentMethod, 
            PlatformFee, EmailConfiguration
        )
        # Import admin configurations
        from .admin_dynamic_config import (
            DynamicConfigurationAdmin, ConfigurationHistoryAdmin, 
            ConfigurationTemplateAdmin
        )
        from .admin_config import (
            SystemConfigurationAdmin, BankAccountAdmin, 
            PaymentMethodAdmin, PlatformFeeAdmin, EmailConfigurationAdmin
        )
