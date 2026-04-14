#!/usr/bin/env python
"""
Final fix for UUIDField lookup error
"""

import re

def fix_service_providers_view():
    """Fix the service_providers view to use min_rating_filter instead of rating"""
    file_path = 'gigs/views.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix GET parameter references
        content = re.sub(r'request\.GET\.get\("rating"\)', 'request.GET.get("min_rating")', content)
        
        # Fix POST parameter references  
        content = re.sub(r'request\.POST\.get\("rating"\)', 'request.POST.get("min_rating")', content)
        
        # Fix form field name references
        content = re.sub(r'name="rating"', 'name="min_rating"', content)
        
        # Fix template variable references
        content = re.sub(r'rating_filter', 'min_rating_filter', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed service_providers view")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function"""
    success = fix_service_providers_view()
    
    if success:
        print("🎉 UUIDField lookup error has been fixed!")
        print("📝 The service_providers view now uses 'min_rating_filter' instead of 'rating'")
        print("🚀 You can now test the service providers page without UUIDField errors!")
    else:
        print("❌ Fix failed - please check the error message above")

if __name__ == '__main__':
    main()
