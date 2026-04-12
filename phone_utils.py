"""
Phone Number Utilities
Simple functions for phone validation and WhatsApp formatting
"""

import re
from typing import Tuple

def validate_phone_number(phone: str) -> Tuple[bool, str, str]:
    """
    Validate and format phone number
    
    Args:
        phone: Raw phone number
        
    Returns:
        Tuple of (is_valid, formatted_number, error_message)
    """
    if not phone:
        return False, "", "Phone number is required"
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    if not cleaned:
        return False, "", "Invalid phone number format"
    
    # Format for WhatsApp
    formatted = format_for_whatsapp(cleaned)
    
    if formatted:
        return True, formatted, ""
    else:
        return False, "", "Invalid phone number format"

def format_for_whatsapp(phone: str) -> str:
    """
    Format phone number for WhatsApp compatibility
    
    Args:
        phone: Raw phone number
        
    Returns:
        WhatsApp-compatible phone number
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Handle South African numbers
    if cleaned.startswith('+27') and len(cleaned) == 12:
        return cleaned
    elif cleaned.startswith('0') and len(cleaned) == 10:
        return '+27' + cleaned[1:]
    elif len(cleaned) == 9 and cleaned[0] in ['6', '7', '8']:
        return '+27' + cleaned
    
    # Return as-is if no pattern matches
    return cleaned
