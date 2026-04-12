#!/usr/bin/env python
import os

# Read the template file
with open('templates/gigs/provider_quotations.html', 'r') as f:
    content = f.read()

# Replace the problematic line
old_line = '{% with user_response=quotation.responses.all|first %}'
new_line = '{% with user_response=quotation.responses.all|first %}'

content = content.replace(old_line, new_line)

# Write back to file
with open('templates/gigs/provider_quotations.html', 'w') as f:
    f.write(content)

print("Template fixed successfully!")
