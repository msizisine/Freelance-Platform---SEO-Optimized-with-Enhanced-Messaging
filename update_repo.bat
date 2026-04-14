@echo off
echo Updating repository with changes (excluding settings files)...
echo.

echo 1. Checking git status...
git status
echo.

echo 2. Adding specific changed files (excluding settings files)...
git add gigs/views.py
git add templates/gigs/service_providers.html
git add templates/gigs/gig_detail.html
echo.

echo 3. Creating descriptive commit...
git commit -m "Fix critical UUIDField lookup error and template syntax issues

MAJOR FIXES:
- Fixed FieldError: Unsupported lookup 'rating' for UUIDField in service providers view
- Resolved TemplateSyntaxError: Invalid block tag 'static' in gig_detail.html

DETAILED CHANGES:
gigs/views.py:
  - Replaced problematic Avg('reviews_received__rating') annotation with manual calculation
  - Fixed field reference from 'gig_set' to 'hired_jobs' 
  - Changed parameter names: 'rating' -> 'provider_rating', 'rating_desc' -> 'avg_rating_desc'
  - Implemented consistent list-based filtering and sorting approach
  - Added manual avg_rating calculation for each provider to avoid UUIDField conflicts

templates/gigs/service_providers.html:
  - Updated form field name from 'min_rating' to 'provider_rating'
  - Changed sort options from 'rating_desc'/'rating_asc' to 'avg_rating_desc'/'avg_rating_asc'
  - Updated template variables to match view parameter names

templates/gigs/gig_detail.html:
  - Added missing %% load static %% tag to resolve template syntax error

VERIFIED:
- Service providers page loads without UUIDField lookup errors
- Gig detail pages load without template syntax errors  
- All filtering and sorting functionality working correctly
- Django development server running successfully"
echo.

echo 4. Pushing to remote repository...
git push origin main
echo.

echo Repository update completed!
pause
