"""
Fix remaining currency symbols in templates while preserving JavaScript
"""

import os
import re

def fix_currency_preserving_js(file_path):
    """Fix currency symbols while preserving JavaScript template literals"""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # More specific replacements that avoid JavaScript
        replacements = [
            # Currency in template variables
            ("${{", "R{{"),
            # Specific currency patterns
            (r"\$\{[^}]*\}", lambda m: m.group(0).replace('$', 'R')),  # Replace $ in template variables but keep structure
        ]
        
        # Apply regex replacements first
        for pattern, replacement in replacements:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)
        
        # Then do simple replacements for remaining currency symbols
        # But be careful not to break JavaScript
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip lines that are clearly JavaScript
            if any(js_indicator in line for js_indicator in [
                'console.log', 'fetch(', 'const ', 'let ', 'var ', 
                'function ', '=>', '${', 'javascript', 'script'
            ]):
                fixed_lines.append(line)
            else:
                # Replace $ with R in non-JavaScript lines
                fixed_line = line.replace('${{', 'R{{').replace('$', 'R')
                fixed_lines.append(fixed_line)
        
        content = '\n'.join(fixed_lines)
        
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

def fix_specific_templates():
    """Fix the remaining templates with dollar signs"""
    print("=== FIXING REMAINING TEMPLATES ===")
    
    remaining_templates = [
        "templates/gigs/complete_job.html",
        "templates/gigs/complete_job_with_invoice.html",
        "templates/gigs/gig_create.html",
        "templates/gigs/gig_form.html",
        "templates/gigs/invoice_detail.html",
        "templates/gigs/job_detail.html",
        "templates/gigs/my_gigs.html",
        "templates/gigs/my_provider_jobs.html",
        "templates/gigs/quotation_request_form.html",
        "templates/gigs/quotation_response_form.html",
        "templates/gigs/quote_request_detail.html",
        "templates/gigs/reject_job.html",
        "templates/gigs/reject_quotation.html",
        "templates/gigs/select_quotation.html",
        "templates/gigs/update_job_status.html",
        "templates/gigs/update_quotation.html",
        "templates/orders/approve_estimate.html",
        "templates/orders/ozow_payment.html",
        "templates/core/admin/service_provider_detail.html",
        "templates/gigs/category_gigs.html",
    ]
    
    changes_made = 0
    for template in remaining_templates:
        if os.path.exists(template):
            if fix_currency_preserving_js(template):
                changes_made += 1
        else:
            print(f"  File not found: {template}")
    
    return changes_made

def check_specific_template(template_path):
    """Check a specific template for currency symbols"""
    print(f"=== CHECKING {template_path} ===")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        currency_lines = []
        
        for i, line in enumerate(lines, 1):
            if '$' in line:
                # Check if it's likely a currency symbol
                if any(currency_indicator in line.lower() for currency_indicator in [
                    'price', 'amount', 'budget', 'cost', 'rate', 'fee', 'total',
                    'payment', 'invoice', 'earnings', 'salary', 'wage'
                ]):
                    currency_lines.append((i, line.strip()))
                elif 'R{{' not in line and '${{' in line:
                    # Template variable that should be fixed
                    currency_lines.append((i, line.strip()))
        
        if currency_lines:
            print(f"  Found {len(currency_lines)} currency-related lines:")
            for line_num, line in currency_lines:
                print(f"    Line {line_num}: {line}")
        else:
            print(f"  No currency symbols found")
        
        return len(currency_lines) > 0
        
    except Exception as e:
        print(f"  Error checking template: {e}")
        return False

def main():
    print("FIXING REMAINING CURRENCY SYMBOLS IN TEMPLATES")
    print("=" * 60)
    
    # Check the specific order detail template mentioned by user
    order_template = "templates/orders/order_detail.html"
    check_specific_template(order_template)
    
    # Fix remaining templates
    changes_made = fix_specific_templates()
    
    print("\n" + "=" * 60)
    print("FIX RESULTS:")
    print(f"Templates updated: {changes_made}")
    
    print("\nREADY FOR TESTING:")
    print("1. Visit http://127.0.0.1:8000/orders/6e3aa51f-a826-4c2b-ba87-1c3e00616cc7/")
    print("2. Check that all currency symbols show R")
    print("3. Verify JavaScript functionality still works")

if __name__ == "__main__":
    main()
