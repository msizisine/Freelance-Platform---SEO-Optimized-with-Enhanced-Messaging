#!/usr/bin/env python
"""
Script to fix UUIDField lookup error by identifying all rating references
"""

import os
import re

def find_rating_references(directory):
    """Find all files that reference 'rating' parameter"""
    rating_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Look for rating parameter references
                        if 'rating' in content:
                            # Check if it's a GET parameter or form field
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if ('rating' in line and 
                                    ('request.GET.get' in line or 'request.POST.get' in line or
                                     'name="rating"' in line)):
                                    rating_files.append({
                                        'file': file_path,
                                        'line': i,
                                        'content': line.strip()
                                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return rating_files

def main():
    """Main function to find and fix rating references"""
    print("🔍 Searching for rating parameter references...")
    
    # Search in gigs directory
    gigs_dir = 'gigs'
    rating_files = find_rating_references(gigs_dir)
    
    if rating_files:
        print(f"\n❌ Found {len(rating_files)} rating references that need fixing:")
        for file_info in rating_files:
            print(f"  📁 {file_info['file']}")
            print(f"     Line {file_info['line']}: {file_info['content']}")
            print(f"     Suggested fix: Change 'rating' to 'min_rating' or 'max_rating'")
        
        print(f"\n🔧 Auto-fix suggestions:")
        print("1. Change request.GET.get('rating') to request.GET.get('min_rating')")
        print("2. Change request.POST.get('rating') to request.POST.get('min_rating')")
        print("3. Change name='rating' to name='min_rating' in HTML forms")
        print("4. Change {% if rating_filter %} to {% if min_rating_filter %} in templates")
        
        print(f"\n📝 Generating fix script...")
        
        # Generate fix script
        fix_script = generate_fix_script(rating_files)
        
        # Save fix script
        with open('fix_rating_references.py', 'w', encoding='utf-8') as f:
            f.write(fix_script)
        
        print(f"✅ Fix script saved as 'fix_rating_references.py'")
        print(f"🚀 Run: python fix_rating_references.py")
        print(f"📋 Then restart Django server")
    else:
        print("✅ No rating references found!")

def generate_fix_script(rating_files):
    """Generate a script to fix all rating references"""
    script = """#!/usr/bin/env python
\"\"\"
Auto-fix script for rating parameter references
\"\"\"

import re
import os

# Files to fix
files_to_fix = [
"""
    
    for file_info in rating_files:
        file_path = file_info['file']
        line_num = file_info['line']
        
        script += f'''
# Fix: {file_path}
with open('{file_path}', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Replace rating parameter with min_rating
content = re.sub(
    r"request\\.GET\\.get\\('rating'\\)",
    "request.GET.get('min_rating'",
    content
)

content = re.sub(
    r"request\\.POST\\.get\\('rating'\\)",
    "request.POST.get('min_rating'",
    content
)

content = re.sub(
    r'name="rating"',
    'name="min_rating"',
    content
)

content = re.sub(
    r'{% if rating_filter %}',
    r'{% if min_rating_filter %}',
    content
)

content = re.sub(
    r'rating_filter',
    'min_rating_filter',
    content
)

with open('{file_path}', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed: {file_path}")
"""
    
    return script

if __name__ == '__main__':
    main()
