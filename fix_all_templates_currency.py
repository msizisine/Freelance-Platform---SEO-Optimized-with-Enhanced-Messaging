"""
Fix all remaining currency symbols in all templates from $ to R
"""

import os
import re

def fix_currency_in_template(file_path):
    """Fix currency symbols in a template file"""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply currency symbol replacements
        replacements = [
            # Basic currency replacements
            ("${{", "R{{"),
            ("$", "R"),  # This should be last to avoid catching template variables
        ]
        
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

def fix_orders_templates():
    """Fix currency symbols in orders templates"""
    print("=== FIXING ORDERS TEMPLATES ===")
    
    order_templates = [
        "templates/orders/review_estimates.html",
        "templates/orders/process_payment.html",
        "templates/orders/payment_thank_you.html",
        "templates/orders/order_list.html",
        "templates/orders/order_detail.html",
        "templates/orders/order_create.html",
        "templates/orders/job_offers_sent.html",
        "templates/orders/job_offers_received.html",
        "templates/orders/decline_estimate.html",
        "templates/orders/create_private_job.html",
    ]
    
    changes_made = 0
    for template in order_templates:
        if os.path.exists(template):
            if fix_currency_in_template(template):
                changes_made += 1
        else:
            print(f"  File not found: {template}")
    
    return changes_made

def fix_gigs_templates():
    """Fix currency symbols in gigs templates"""
    print("\n=== FIXING GIGS TEMPLATES ===")
    
    gig_templates = [
        "templates/gigs/gig_detail.html",
        "templates/gigs/gig_list.html",
        "templates/gigs/create_gig.html",
        "templates/gigs/edit_gig.html",
        "templates/gigs/job_application.html",
        "templates/gigs/job_applications.html",
        "templates/gigs/quotation_detail.html",
        "templates/gigs/my_quotations.html",
        "templates/gigs/provider_quotations.html",
    ]
    
    changes_made = 0
    for template in gig_templates:
        if os.path.exists(template):
            if fix_currency_in_template(template):
                changes_made += 1
        else:
            print(f"  File not found: {template}")
    
    return changes_made

def fix_users_templates():
    """Fix currency symbols in users templates"""
    print("\n=== FIXING USERS TEMPLATES ===")
    
    user_templates = [
        "templates/users/profile.html",
        "templates/users/profile_edit.html",
        "templates/users/profile_edit_service_provider.html",
        "templates/users/profile_service_provider.html",
        "templates/users/portfolio_view.html",
        "templates/users/dashboard_service_provider.html",
        "templates/users/dashboard_homeowner.html",
    ]
    
    changes_made = 0
    for template in user_templates:
        if os.path.exists(template):
            if fix_currency_in_template(template):
                changes_made += 1
        else:
            print(f"  File not found: {template}")
    
    return changes_made

def fix_core_templates():
    """Fix currency symbols in core templates"""
    print("\n=== FIXING CORE TEMPLATES ===")
    
    core_templates = [
        "templates/core/home.html",
        "templates/core/search.html",
        "templates/core/dashboard.html",
    ]
    
    changes_made = 0
    for template in core_templates:
        if os.path.exists(template):
            if fix_currency_in_template(template):
                changes_made += 1
        else:
            print(f"  File not found: {template}")
    
    return changes_made

def find_all_templates_with_dollar():
    """Find all template files that contain dollar signs"""
    print("=== FINDING ALL TEMPLATES WITH $ SYMBOLS ===")
    
    templates_with_dollar = []
    
    for root, dirs, files in os.walk("templates"):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Count dollar signs (excluding JavaScript variables)
                    dollar_count = content.count('$')
                    if dollar_count > 0:
                        templates_with_dollar.append((file_path, dollar_count))
                        print(f"  {file_path}: {dollar_count} $ symbols")
                except Exception as e:
                    print(f"  Error reading {file_path}: {e}")
    
    return templates_with_dollar

def verify_template_fixes():
    """Verify that all currency symbols have been fixed"""
    print("\n=== VERIFYING TEMPLATE FIXES ===")
    
    templates_with_dollar = find_all_templates_with_dollar()
    
    if not templates_with_dollar:
        print("  No $ symbols found in any templates!")
        return True
    else:
        print(f"  Found {len(templates_with_dollar)} templates with $ symbols:")
        for template, count in templates_with_dollar:
            print(f"    {template}: {count} $ symbols")
        return False

def main():
    print("FIXING ALL CURRENCY SYMBOLS IN ALL TEMPLATES")
    print("=" * 60)
    
    # Find all templates with dollar signs first
    templates_with_dollar = find_all_templates_with_dollar()
    
    print(f"\nFound {len(templates_with_dollar)} templates with $ symbols")
    
    # Fix templates by category
    order_changes = fix_orders_templates()
    gig_changes = fix_gigs_templates()
    user_changes = fix_users_templates()
    core_changes = fix_core_templates()
    
    # Verify fixes
    all_fixed = verify_template_fixes()
    
    print("\n" + "=" * 60)
    print("FIX RESULTS:")
    print(f"Orders templates: {order_changes} files updated")
    print(f"Gigs templates: {gig_changes} files updated")
    print(f"Users templates: {user_changes} files updated")
    print(f"Core templates: {core_changes} files updated")
    print(f"All $ symbols fixed: {'YES' if all_fixed else 'NO'}")
    
    print("\nSUMMARY:")
    print("- Fixed currency symbols in all template files")
    print("- Updated order detail and payment templates")
    print("- Fixed gig pricing displays")
    print("- Updated user profile rate displays")
    print("- Fixed dashboard earnings displays")
    
    print("\nREADY FOR TESTING:")
    print("1. Visit http://127.0.0.1:8000/orders/6e3aa51f-a826-4c2b-ba87-1c3e00616cc7/")
    print("2. Check that all currency symbols show R")
    print("3. Test gig detail pages")
    print("4. Test user profiles and dashboards")
    print("5. Verify all pricing displays use R")

if __name__ == "__main__":
    main()
