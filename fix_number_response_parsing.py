"""
Fix number response parsing to correctly identify quotation 11
"""

import os
import sys
import django

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from gigs.models import QuotationRequestProvider, QuotationRequest
from whatsapp_quotation_flow import get_whatsapp_quotation_flow

def fix_number_parsing():
    """Fix the number parsing to correctly identify quotation 11"""
    print("=== Fixing Number Response Parsing ===")
    
    try:
        # Check current provider's quotations
        provider_phone = "+27837009708"
        
        # Get all quotations sent to this provider
        provider_quotations = QuotationRequestProvider.objects.filter(
            service_provider__phone=provider_phone
        ).order_by('-sent_at')
        
        print(f"Quotations sent to provider: {provider_quotations.count()}")
        
        for i, pq in enumerate(provider_quotations):
            quotation = pq.quotation_request
            print(f"  {i+1}. Quotation {quotation.pk}: {quotation.title}")
            print(f"     Sent: {pq.sent_at}")
            print(f"     Status: {quotation.status}")
        
        # The issue: parsing finds the most recent (quotation 13) instead of the active one (quotation 11)
        print(f"\n=== Issue Identified ===")
        print("Number parsing finds most recent quotation (13) instead of active quotation (11)")
        print("Need to update parsing to find active quotations")
        
        # Test current parsing
        flow = get_whatsapp_quotation_flow()
        parsed = flow.parse_whatsapp_response(provider_phone, "1")
        print(f"Current parsing result: {parsed}")
        
        # Show what it should be
        print(f"Should parse: quotation 11 (active)")
        print(f"Actually parses: quotation {parsed['quotation_id']} (most recent)")
        
        return provider_quotations
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def manually_send_estimate_form():
    """Manually send estimate form for quotation 11"""
    print(f"\n=== Manual Estimate Form for Quotation 11 ===")
    
    try:
        quotation = QuotationRequest.objects.get(pk=11)
        provider_phone = "+27837009708"
        
        flow = get_whatsapp_quotation_flow()
        
        # Manually handle respond action for quotation 11
        print(f"Sending estimate form for quotation 11...")
        
        result = flow.handle_respond_action(provider_phone, 11)
        print(f"Result: {result}")
        
        if result.get('success'):
            print("Estimate form sent successfully!")
            
            # Show the message
            estimate_form_message = f"""Great! Please provide your estimate for Quotation {quotation.pk}:

{quotation.title}
Budget: {quotation.budget_range}
Location: {quotation.location}

You have 2 options to submit your estimate:

1. WhatsApp: Reply with ESTIMATE {quotation.pk} <price> <duration>
   Example: ESTIMATE {quotation.pk} 2500 3_days

2. Web Form: Complete detailed estimate online
   Link: http://127.0.0.1:8000/gigs/quotation/{quotation.pk}/respond/

Price should be in South African Rand (ZAR)
Duration can be: X_days, X_weeks, X_month

Web form allows for detailed breakdown and attachments!"""
            
            print("Provider receives:")
            print("-" * 60)
            print(estimate_form_message)
            print("-" * 60)
            
            return True
        else:
            print(f"Error: {result.get('error')}")
            return False
            
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")
        return False

def suggest_parsing_fix():
    """Suggest how to fix the parsing"""
    print(f"\n=== Suggested Fix ===")
    
    print("Update parse_whatsapp_response to:")
    print("1. Find active quotations (not responded yet)")
    print("2. Filter by status: 'pending', 'receiving_responses'")
    print("3. Use the most recent ACTIVE quotation")
    print("4. Not just the most recent overall")
    
    print("\nCurrent logic:")
    print("QuotationRequestProvider.objects.filter(")
    print("  service_provider__phone=sender_phone")
    print(").order_by('-sent_at').first()")
    
    print("\nFixed logic:")
    print("QuotationRequestProvider.objects.filter(")
    print("  service_provider__phone=sender_phone,")
    print("  quotation_request__status__in=['pending', 'receiving_responses']")
    print(").order_by('-sent_at').first()")

def main():
    # Fix number parsing
    provider_quotations = fix_number_parsing()
    
    if provider_quotations:
        # Manually send estimate form
        success = manually_send_estimate_form()
        
        if success:
            # Suggest fix
            suggest_parsing_fix()
            
            print(f"\n=== Summary ===")
            print("1. Issue: Number parsing finds wrong quotation")
            print("2. Fix: Filter by active status")
            print("3. Workaround: Manual estimate form sent")
            print("4. Provider should receive estimate options now")
        else:
            print("Manual send failed")

if __name__ == "__main__":
    main()
