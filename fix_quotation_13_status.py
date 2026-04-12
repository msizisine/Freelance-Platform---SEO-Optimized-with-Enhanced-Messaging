"""
Fix quotation 13 status to properly reflect WhatsApp response
"""

import os
import sys
import django

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from gigs.models import QuotationRequest, QuotationResponse, QuotationRequestProvider

def fix_quotation_13_status():
    """Fix quotation 13 status to evaluation_period since all providers responded"""
    print("=== Fixing Quotation 13 Status ===")
    
    try:
        quotation = QuotationRequest.objects.get(pk=13)
        print(f"Current status: {quotation.status}")
        
        # Count providers and responses
        total_providers = QuotationRequestProvider.objects.filter(quotation_request=quotation).count()
        total_responses = QuotationResponse.objects.filter(quotation_request=quotation).count()
        
        print(f"Providers: {total_providers}")
        print(f"Responses: {total_responses}")
        
        if total_responses >= total_providers:
            quotation.status = 'evaluation_period'
            quotation.save()
            print(f"Updated status to: {quotation.status}")
        else:
            print(f"Status update not needed - not all providers responded")
        
        # Show the response details
        responses = QuotationResponse.objects.filter(quotation_request=quotation)
        for response in responses:
            print(f"\nResponse from {response.service_provider.email}:")
            print(f"  Price: R{response.estimated_price}")
            print(f"  Status: {response.status}")
            print(f"  WhatsApp: {'Yes' if 'Submitted via WhatsApp' in response.notes else 'No'}")
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 13 not found")

if __name__ == "__main__":
    fix_quotation_13_status()
