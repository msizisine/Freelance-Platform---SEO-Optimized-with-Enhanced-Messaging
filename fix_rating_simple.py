#!/usr/bin/env python
"""
Simple script to fix rating parameter references
"""

import os
import re

def fix_file(file_path):
    """Fix rating parameter references in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix GET parameter references
        content = re.sub(
            r"request\.GET\.get\('rating'\)",
            "request.GET.get('min_rating')",
            content
        )
        
        # Fix POST parameter references
        content = re.sub(
            r"request\.POST\.get\('rating'\)",
            "request.POST.get('min_rating')",
            content
        )
        
        # Fix form field name references
        content = re.sub(
            r'name="rating"',
            'name="min_rating"',
            content
        )
        
        # Fix template variable references
        content = re.sub(
            r'{% if rating_filter %}',
            '{% if min_rating_filter %}',
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed: {file_path}")
        return True
    
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all rating references in service_providers view"""
    files_to_fix = [
        'gigs/views.py',
        'gigs/templates/service_providers.html'
    ]
    
    all_fixed = True
    for file_path in files_to_fix:
        if not fix_file(file_path):
            all_fixed = False
    
    if all_fixed:
        print("✅ All rating references fixed successfully!")
    else:
        print("❌ Some files could not be fixed")

if __name__ == '__main__':
    main()
