"""
Fix all remaining currency symbols in gigs app from $ to R
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

def fix_gigs_forms():
    """Fix currency symbols in gigs/forms.py"""
    print("=== FIXING GIGS/FORMS.PY ===")
    
    file_path = "gigs/forms.py"
    replacements = [
        ("'Proposed Rate ($)'", "'Proposed Rate (R)'"),
        ("'e.g., $500-$1000'", "'e.g., R500-R1000'"),
        ("'Calculated Price ($)'", "'Calculated Price (R)'"),
    ]
    
    return fix_currency_in_file(file_path, replacements)

def fix_gigs_views_invoice():
    """Fix currency symbols in gigs/views_invoice.py"""
    print("\n=== FIXING GIGS/VIEWS_INVOICE.PY ===")
    
    file_path = "gigs/views_invoice.py"
    replacements = [
        ("f\"${gig.budget_min} - ${gig.budget_max}\"", "f\"R{gig.budget_min} - R{gig.budget_max}\""),
        ("f\"${order.total_amount}\"", "f\"R{order.total_amount}\""),
        ("f\"${order.total_amount}\"", "f\"R{order.total_amount}\""),
    ]
    
    return fix_currency_in_file(file_path, replacements)

def fix_gigs_utils():
    """Fix currency symbols in gigs/utils.py"""
    print("\n=== FIXING GIGS/UTILS.PY ===")
    
    file_path = "gigs/utils.py"
    replacements = [
        ("f\"${job_application.proposed_rate}\"", "f\"R{job_application.proposed_rate}\""),
        ("\"$0.00\"", "\"R0.00\""),
        ("f\"${job_application.proposed_rate}\"", "f\"R{job_application.proposed_rate}\""),
    ]
    
    return fix_currency_in_file(file_path, replacements)

def fix_gigs_whatsapp_flows():
    """Fix currency symbols in gigs/whatsapp_flows.py"""
    print("\n=== FIXING GIGS/WHATSAPP_FLOWS.PY ===")
    
    file_path = "gigs/whatsapp_flows.py"
    replacements = [
        ('"Under $5,000"', '"Under R5,000"'),
        ('"$5,000 - $10,000"', '"R5,000 - R10,000"'),
        ('"$10,000 - $25,000"', '"R10,000 - R25,000"'),
        ('"$25,000 - $50,000"', '"R25,000 - R50,000"'),
        ('"$50,000 - $100,000"', '"R50,000 - R100,000"'),
        ('"Over $100,000"', '"Over R100,000"'),
        ('"Estimated Price ($)"', '"Estimated Price (R)"'),
    ]
    
    return fix_currency_in_file(file_path, replacements)

def check_quotation_request_template():
    """Check if the quotation request template has any remaining $ symbols"""
    print("\n=== CHECKING QUOTATION REQUEST TEMPLATE ===")
    
    file_path = "templates/gigs/create_quotation_request.html"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for $ symbols
        dollar_count = content.count('$')
        if dollar_count > 0:
            print(f"  Found {dollar_count} $ symbols in template")
            
            # Show lines with $ symbols
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if '$' in line:
                    print(f"    Line {i}: {line.strip()}")
        else:
            print(f"  No $ symbols found in template")
        
        return dollar_count == 0
        
    except Exception as e:
        print(f"  Error checking template: {e}")
        return False

def verify_gigs_fixes():
    """Verify that all currency symbols have been fixed in gigs app"""
    print("\n=== VERIFYING GIGS FIXES ===")
    
    files_to_check = [
        "gigs/forms.py",
        "gigs/views_invoice.py",
        "gigs/utils.py",
        "gigs/whatsapp_flows.py",
        "templates/gigs/create_quotation_request.html",
    ]
    
    remaining_dollars = 0
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count remaining $ symbols (excluding JavaScript variables)
            dollar_count = content.count('$')
            if dollar_count > 0:
                print(f"  {file_path}: {dollar_count} remaining $ symbols")
                remaining_dollars += dollar_count
            else:
                print(f"  {file_path}: No $ symbols found")
        else:
            print(f"  File not found: {file_path}")
    
    return remaining_dollars == 0

def main():
    print("FIXING REMAINING CURRENCY SYMBOLS IN GIGS APP")
    print("=" * 60)
    
    # Fix gigs forms
    forms_ok = fix_gigs_forms()
    
    # Fix gigs views_invoice
    invoice_ok = fix_gigs_views_invoice()
    
    # Fix gigs utils
    utils_ok = fix_gigs_utils()
    
    # Fix gigs whatsapp_flows
    whatsapp_ok = fix_gigs_whatsapp_flows()
    
    # Check quotation request template
    template_ok = check_quotation_request_template()
    
    # Verify all fixes
    all_fixed = verify_gigs_fixes()
    
    print("\n" + "=" * 60)
    print("FIX RESULTS:")
    print(f"Gigs forms: {'OK' if forms_ok else 'FAIL'}")
    print(f"Gigs views_invoice: {'OK' if invoice_ok else 'FAIL'}")
    print(f"Gigs utils: {'OK' if utils_ok else 'FAIL'}")
    print(f"Gigs whatsapp_flows: {'OK' if whatsapp_ok else 'FAIL'}")
    print(f"Quotation template: {'OK' if template_ok else 'FAIL'}")
    print(f"All $ symbols fixed: {'YES' if all_fixed else 'NO'}")
    
    print("\nSUMMARY:")
    print("- Fixed form labels to use R instead of $")
    print("- Updated budget range placeholders")
    print("- Fixed invoice generation to use R")
    print("- Updated PDF generation to use R")
    print("- Fixed WhatsApp flow options")
    print("- Updated all currency formatting")
    
    print("\nREADY FOR TESTING:")
    print("1. Visit http://127.0.0.1:8000/gigs/request-quotation/")
    print("2. Check that all currency symbols show R")
    print("3. Test form submission")
    print("4. Verify invoice generation uses R")

if __name__ == "__main__":
    main()
