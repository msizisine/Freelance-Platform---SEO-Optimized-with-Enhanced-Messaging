"""
Phone Number Utilities
Handles validation, formatting, and conversion of phone numbers for WhatsApp compatibility
"""

import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class PhoneNumberUtils:
    """Utility class for phone number validation and formatting"""
    
    # South African phone number patterns
    SOUTH_AFRICA_PATTERNS = {
        'local': re.compile(r'^0?([6-8]\d{8})$'),  # 0837009708 or 837009708
        'international': re.compile(r'^\+27([6-8]\d{8})$'),  # +27837009708
        'with_spaces': re.compile(r'^0?([6-8]\d{2})\s?(\d{3})\s?(\d{3})$'),  # 083 700 9708
        'with_hyphens': re.compile(r'^0?([6-8]\d{2})-?(\d{3})-?(\d{3})$'),  # 083-700-9708
    }
    
    @classmethod
    def clean_phone_number(cls, phone: str) -> str:
        """
        Clean and standardize phone number
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Cleaned phone number string
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Remove leading 00 if present (international dialing prefix)
        if cleaned.startswith('00'):
            cleaned = '+' + cleaned[2:]
        
        return cleaned.strip()
    
    @classmethod
    def is_valid_south_african_number(cls, phone: str) -> bool:
        """
        Check if phone number is valid South African format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid South African number
        """
        cleaned = cls.clean_phone_number(phone)
        
        # Check against patterns
        for pattern_name, pattern in cls.SOUTH_AFRICA_PATTERNS.items():
            if pattern.match(cleaned):
                return True
        
        # Check international format
        if cleaned.startswith('+27') and len(cleaned) == 12:
            return True
            
        return False
    
    @classmethod
    def format_for_whatsapp(cls, phone: str) -> str:
        """
        Format phone number for WhatsApp compatibility
        
        Args:
            phone: Raw phone number
            
        Returns:
            WhatsApp-compatible phone number or empty string if invalid
        """
        if not phone:
            return ""
        
        cleaned = cls.clean_phone_number(phone)
        
        # If already in international format, validate and return
        if cleaned.startswith('+'):
            if cls.is_valid_south_african_number(cleaned):
                return cleaned
            else:
                logger.warning(f"Invalid international format: {cleaned}")
                return ""
        
        # Convert South African local format to international
        for pattern_name, pattern in cls.SOUTH_AFRICA_PATTERNS.items():
            match = pattern.match(cleaned)
            if match:
                if pattern_name == 'local':
                    # 0837009708 -> +27837009708
                    digits = match.group(1)
                    return f'+27{digits}'
                elif pattern_name == 'with_spaces' or pattern_name == 'with_hyphens':
                    # 083 700 9708 -> +27837009708
                    digits = match.group(1) + match.group(2) + match.group(3)
                    return f'+27{digits}'
                elif pattern_name == 'international':
                    # +27837009708 -> +27837009708 (already correct)
                    return cleaned
        
        # If no pattern matches, try to detect South African numbers
        if len(cleaned) == 9 and cleaned[0] in ['6', '7', '8']:
            # Assume it's a South African number without leading 0
            return f'+27{cleaned}'
        
        logger.warning(f"Could not format phone number for WhatsApp: {phone}")
        return ""
    
    @classmethod
    def validate_and_format(cls, phone: str) -> Tuple[bool, str, str]:
        """
        Validate and format phone number
        
        Args:
            phone: Raw phone number
            
        Returns:
            Tuple of (is_valid, formatted_number, error_message)
        """
        if not phone:
            return False, "", "Phone number is required"
        
        cleaned = cls.clean_phone_number(phone)
        
        if not cleaned:
            return False, "", "Invalid phone number format"
        
        # Try to format for WhatsApp
        formatted = cls.format_for_whatsapp(cleaned)
        
        if formatted:
            return True, formatted, ""
        else:
            return False, "", "Invalid South African phone number. Please enter a number starting with 0 (e.g., 0837009708)"
    
    @classmethod
    def format_display(cls, phone: str) -> str:
        """
        Format phone number for display purposes
        
        Args:
            phone: Phone number (should be in international format)
            
        Returns:
            Human-readable format
        """
        if not phone:
            return ""
        
        cleaned = cls.clean_phone_number(phone)
        
        # If international format, convert to local display format
        if cleaned.startswith('+27') and len(cleaned) == 12:
            local = '0' + cleaned[3:]
            # Format as 083 700 9708
            if len(local) == 9:
                return f"{local[:3]} {local[3:6]} {local[6:]}"
        
        return cleaned
    
    @classmethod
    def get_phone_number_stats(cls) -> dict:
        """
        Get statistics about phone numbers in the system
        
        Returns:
            Dictionary with phone number statistics
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        stats = {
            'total_users': User.objects.count(),
            'users_with_phones': 0,
            'valid_phones': 0,
            'invalid_phones': 0,
            'formatted_phones': 0,
            'issues': []
        }
        
        for user in User.objects.all():
            if user.phone:
                stats['users_with_phones'] += 1
                
                is_valid, formatted, error = cls.validate_and_format(user.phone)
                
                if is_valid:
                    stats['valid_phones'] += 1
                    if user.phone != formatted:
                        stats['formatted_phones'] += 1
                else:
                    stats['invalid_phones'] += 1
                    stats['issues'].append({
                        'user': user.email,
                        'phone': user.phone,
                        'error': error
                    })
        
        return stats

# Convenience functions
def clean_phone_number(phone: str) -> str:
    """Clean phone number"""
    return PhoneNumberUtils.clean_phone_number(phone)

def format_for_whatsapp(phone: str) -> str:
    """Format phone number for WhatsApp"""
    return PhoneNumberUtils.format_for_whatsapp(phone)

def validate_phone_number(phone: str) -> Tuple[bool, str, str]:
    """Validate phone number"""
    return PhoneNumberUtils.validate_and_format(phone)

def format_display_phone(phone: str) -> str:
    """Format phone for display"""
    return PhoneNumberUtils.format_display(phone)
