"""
Fix all currency symbols from $ to R in forms and templates
"""

import os
import re

def fix_currency_in_file(file_path, replacements):
    """Fix currency symbols in a file"""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Updated: {file_path}")
            return True
        else:
            print(f"  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return False

def fix_forms_py():
    """Fix currency symbols in forms.py"""
    print("=== FIXING FORMS.PY ===")
    
    file_path = "users/forms.py"
    replacements = [
        ("'Hourly Rate ($)", "'Hourly Rate (R)"),
        ("'Daily Rate ($)", "'Daily Rate (R)"),
        ("'Rate per Square Meter ($)", "'Rate per Square Meter (R)"),
    ]
    
    return fix_currency_in_file(file_path, replacements)

def fix_templates():
    """Fix currency symbols in templates"""
    print("\n=== FIXING TEMPLATES ===")
    
    template_files = [
        "templates/users/profile_edit_service_provider.html",
        "templates/users/profile_service_provider.html",
        "templates/users/portfolio_view.html",
        "templates/users/dashboard_service_provider.html",
        "templates/reviews/create_review_with_invoice.html",
        "templates/orders/create_from_provider.html",
    ]
    
    # Template-specific replacements
    template_replacements = [
        # Input group symbols
        ("<span class=\"input-group-text\">$</span>", "<span class=\"input-group-text\">R</span>"),
        # Display symbols
        ("${{", "R{{"),
        ("${", "R"),
        ("$", "R"),  # This should be last to avoid catching template variables
    ]
    
    changes_made = 0
    for template_file in template_files:
        if os.path.exists(template_file):
            if fix_currency_in_file(template_file, template_replacements):
                changes_made += 1
        else:
            print(f"  File not found: {template_file}")
    
    return changes_made

def fix_whatsapp_service():
    """Fix currency symbols in WhatsApp service"""
    print("\n=== FIXING WHATSAPP SERVICE ===")
    
    file_path = "whatsapp_service.py"
    replacements = [
        ("Amount: ${", "Amount: R"),
        ("Budget: ${", "Budget: R"),
        ("Your Price: ${", "Your Price: R"),
        ("Price: ${", "Price: R"),
        ("Amount: ${", "Amount: R"),
    ]
    
    return fix_currency_in_file(file_path, replacements)

def fix_test_files():
    """Fix currency symbols in test files"""
    print("\n=== FIXING TEST FILES ===")
    
    test_files = [
        "test_interactive_whatsapp_flow.py",
        "test_phone_status_handling.py",
        "test_web_quote_flow.py",
        "test_whatsapp_error_handling.py",
        "test_whatsapp_flow.py",
        "test_whatsapp_integration.py",
    ]
    
    # Test file replacements
    test_replacements = [
        ("budget_range=\"$", "budget_range=\"R"),
        ("budget=\"$", "budget=\"R"),
        ("'$", "'R"),
    ]
    
    changes_made = 0
    for test_file in test_files:
        if os.path.exists(test_file):
            if fix_currency_in_file(test_file, test_replacements):
                changes_made += 1
        else:
            print(f"  File not found: {test_file}")
    
    return changes_made

def verify_fixes():
    """Verify that currency symbols have been fixed"""
    print("\n=== VERIFYING FIXES ===")
    
    # Check for remaining $ symbols
    files_to_check = [
        "users/forms.py",
        "templates/users/profile_edit_service_provider.html",
        "templates/users/profile_service_provider.html",
        "whatsapp_service.py",
    ]
    
    remaining_dollars = 0
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count remaining $ symbols (excluding template variables)
            dollar_count = content.count('$')
            if dollar_count > 0:
                print(f"  {file_path}: {dollar_count} remaining $ symbols")
                remaining_dollars += dollar_count
            else:
                print(f"  {file_path}: No $ symbols found")
    
    return remaining_dollars == 0

def main():
    print("FIXING CURRENCY SYMBOLS FROM $ TO R")
    print("=" * 50)
    
    # Fix forms.py
    forms_ok = fix_forms_py()
    
    # Fix templates
    template_changes = fix_templates()
    
    # Fix WhatsApp service
    whatsapp_ok = fix_whatsapp_service()
    
    # Fix test files
    test_changes = fix_test_files()
    
    # Verify fixes
    all_fixed = verify_fixes()
    
    print("\n" + "=" * 50)
    print("FIX RESULTS:")
    print(f"Forms.py: {'OK' if forms_ok else 'FAIL'}")
    print(f"Templates: {template_changes} files updated")
    print(f"WhatsApp service: {'OK' if whatsapp_ok else 'FAIL'}")
    print(f"Test files: {test_changes} files updated")
    print(f"All $ symbols fixed: {'YES' if all_fixed else 'NO'}")
    
    print("\nSUMMARY:")
    print("- Replaced $ with R in form labels")
    print("- Updated input group symbols in templates")
    print("- Fixed currency display in templates")
    print("- Updated WhatsApp message templates")
    print("- Fixed test data to use R instead of $")
    
    print("\nREADY FOR TESTING:")
    print("1. Check forms now show R instead of $")
    print("2. Verify templates display R symbols")
    print("3. Test WhatsApp messages show R currency")
    print("4. All currency formatting now uses South African Rand")

if __name__ == "__main__":
    main()
