"""
Handle provider response "1" and send estimate form
"""

import os
import sys
import django

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from gigs.models import QuotationRequest, QuotationResponse
from whatsapp_quotation_flow import get_whatsapp_quotation_flow

User = get_user_model()

def handle_provider_response_1():
    """Handle provider response "1" and send estimate form"""
    print("=== Handling Provider Response '1' ===")
    
    try:
        quotation = QuotationRequest.objects.get(pk=11)
        provider = User.objects.get(email='msizi34@mobi-cafe.co.za')
        
        print(f"Quotation: {quotation.title}")
        print(f"Provider: {provider.email}")
        print(f"Provider Phone: {provider.phone}")
        
        flow = get_whatsapp_quotation_flow()
        
        # Simulate webhook processing of "1"
        print(f"\n=== Step 1: Parse Response '1' ===")
        
        parsed = flow.parse_whatsapp_response(provider.phone, "1")
        print(f"Parsed: {parsed}")
        
        if parsed['action'] == 'respond':
            print("Response '1' parsed correctly!")
            
            # Step 2: Handle RESPOND action
            print(f"\n=== Step 2: Handle RESPOND Action ===")
            
            result = flow.handle_respond_action(provider.phone, parsed['quotation_id'])
            print(f"Result: {result}")
            
            if result.get('success'):
                print("RESPOND action handled successfully!")
                print("Estimate form sent to provider!")
                
                # Show what provider receives
                print(f"\n=== Step 3: Estimate Form Message ===")
                
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
                
                print("Provider should receive:")
                print("-" * 60)
                print(estimate_form_message)
                print("-" * 60)
                
                # Check if response was created
                response = QuotationResponse.objects.filter(
                    quotation_request=quotation,
                    service_provider=provider
                ).first()
                
                if response:
                    print(f"\n=== Step 4: Response Created ===")
                    print(f"Response ID: {response.pk}")
                    print(f"Status: {response.status}")
                    print(f"Notes: {response.notes}")
                    print(f"Price breakdown: {response.price_breakdown}")
                else:
                    print("No response created yet")
                
                # Check quotation status
                quotation.refresh_from_db()
                print(f"\n=== Step 5: Quotation Status ===")
                print(f"Status: {quotation.status}")
                
                return True
            else:
                print(f"Handle error: {result.get('error')}")
                return False
        else:
            print(f"Parse error: {parsed.get('error')}")
            return False
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")
        return False
    except User.DoesNotExist:
        print("Provider not found")
        return False

def check_webhook_status():
    """Check if webhook would process this correctly"""
    print(f"\n=== Webhook Processing Check ===")
    
    print("Webhook should receive:")
    print("{")
    print("  'data': {")
    print("    'from': '+27837009708',")
    print("    'text': '1',")
    print("    'id': 'message_id_123'")
    print("  }")
    print("}")
    
    print("\nWebhook processing:")
    print("1. Parse message: '1'")
    print("2. Detect number response")
    print("3. Find most recent quotation for provider")
    print("4. Convert to 'respond' action")
    print("5. Call handle_respond_action()")
    print("6. Send estimate form options")

def show_next_provider_actions():
    """Show what provider can do next"""
    print(f"\n=== Next Provider Actions ===")
    
    print("Provider now has 2 options:")
    print("")
    print("OPTION 1 - WhatsApp (Quick):")
    print("Reply: ESTIMATE 11 8000 5_days")
    print("Pros: Fast, simple")
    print("Cons: Limited details")
    print("")
    print("OPTION 2 - Web Form (Detailed):")
    print("Visit: http://127.0.0.1:8000/gigs/quotation/11/respond/")
    print("Pros: Detailed breakdown, attachments")
    print("Cons: Takes more time")
    print("")
    print("Both options will update the quotation status automatically!")

def check_quotation_status():
    """Check current quotation status"""
    print(f"\n=== Current Quotation Status ===")
    
    try:
        quotation = QuotationRequest.objects.get(pk=11)
        
        print(f"Quotation: {quotation.title}")
        print(f"Status: {quotation.status}")
        print(f"Homeowner: {quotation.homeowner.email}")
        
        # Check responses
        responses = QuotationResponse.objects.filter(quotation_request=quotation)
        print(f"Responses: {responses.count()}")
        
        for response in responses:
            print(f"  - {response.service_provider.email}: {response.status}")
            print(f"    Notes: {response.notes}")
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")

def main():
    # Handle provider response
    success = handle_provider_response_1()
    
    if success:
        # Check webhook status
        check_webhook_status()
        
        # Show next actions
        show_next_provider_actions()
        
        # Check quotation status
        check_quotation_status()
        
        print(f"\n=== Response '1' Handled Successfully ===")
        print("Provider should now be receiving estimate options!")
        print("Monitor: http://127.0.0.1:8000/gigs/quotation/11/")

if __name__ == "__main__":
    main()
