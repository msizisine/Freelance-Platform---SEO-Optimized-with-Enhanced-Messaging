"""
Resend WhatsApp message to service provider for quotation 11
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
from gigs.models import QuotationRequest, QuotationRequestProvider
from whatsapp_quotation_flow import get_whatsapp_quotation_flow

User = get_user_model()

def resend_whatsapp_quotation_11():
    """Resend WhatsApp message to providers for quotation 11"""
    print("=== Resending WhatsApp for Quotation 11 ===")
    
    try:
        quotation = QuotationRequest.objects.get(pk=11)
        print(f"Quotation: {quotation.title}")
        print(f"Homeowner: {quotation.homeowner.email}")
        print(f"Status: {quotation.status}")
        
        # Get providers sent to this quotation
        sent_providers = QuotationRequestProvider.objects.filter(
            quotation_request=quotation
        ).select_related('service_provider')
        
        print(f"\nProviders to contact: {sent_providers.count()}")
        
        flow = get_whatsapp_quotation_flow()
        
        for sent_provider in sent_providers:
            provider = sent_provider.service_provider
            print(f"\n--- Contacting Provider: {provider.email} ---")
            print(f"Phone: {provider.phone}")
            print(f"User Type: {provider.user_type}")
            
            if provider.phone:
                print("Sending enhanced WhatsApp message...")
                
                result = flow.send_interactive_quotation_request(
                    to=provider.phone,
                    quotation=quotation,
                    provider=provider
                )
                
                print(f"Result: {result.get('success')}")
                print(f"Message ID: {result.get('message_id')}")
                print(f"Enhanced Format: {result.get('enhanced_format', False)}")
                
                if result.get('success'):
                    print("WhatsApp resent successfully!")
                    print("Provider can now reply with: 1 or RESPOND 11")
                else:
                    print(f"Error: {result.get('error')}")
                    if 'rate limit' in str(result.get('error')).lower():
                        print("Rate limiting active - wait 1 minute")
            else:
                print("No phone number - WhatsApp not available")
                print("Email notification would be sent instead")
        
        # Show what message was sent
        print(f"\n=== WhatsApp Message Content ===")
        message = f"""New Quotation Request - ID: {quotation.pk}

Client: {quotation.homeowner.get_full_name() or quotation.homeowner.email}
Title: {quotation.title}
Description: {quotation.description[:200]}{'...' if len(quotation.description) > 200 else ''}
Budget: {quotation.budget_range}
Location: {quotation.location}
Deadline: {quotation.response_deadline.strftime('%Y-%m-%d') if quotation.response_deadline else 'Not specified'}

Please choose your response:

1) RESPOND {quotation.pk}
   To provide your estimate

2) IGNORE {quotation.pk}  
   To decline this request

Simply reply with the number (1 or 2) or the full command.

This is an automated message from Freelance Platform."""
        
        print("Message that was sent:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        
        return quotation
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")
        return None

def check_provider_responses():
    """Check if any providers have responded after resending"""
    print(f"\n=== Checking Provider Responses ===")
    
    try:
        quotation = QuotationRequest.objects.get(pk=11)
        
        from gigs.models import QuotationResponse
        responses = QuotationResponse.objects.filter(quotation_request=quotation)
        
        print(f"Current responses: {responses.count()}")
        
        for response in responses:
            print(f"\nResponse from: {response.service_provider.email}")
            print(f"Status: {response.status}")
            print(f"Price: R{response.estimated_price}")
            print(f"Duration: {response.estimated_duration}")
            print(f"Submitted: {response.submitted_at}")
            
            if "Submitted via WhatsApp" in response.notes:
                print("Method: WhatsApp response")
            elif "Submitted via web form" in response.notes:
                print("Method: Web form response")
            else:
                print("Method: Dashboard response")
        
        if responses.count() == 0:
            print("No responses yet - providers should be receiving WhatsApp now!")
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")

def show_expected_flow():
    """Show what should happen next"""
    print(f"\n=== Expected Flow After Resend ===")
    
    print("1. Provider receives enhanced WhatsApp message")
    print("2. Provider sees numbered options:")
    print("   1) RESPOND 11")
    print("   2) IGNORE 11")
    print("3. Provider replies with '1' (easiest)")
    print("4. System sends estimate options:")
    print("   - WhatsApp: ESTIMATE 11 <price> <duration>")
    print("   - Web Form: http://127.0.0.1:8000/gigs/quotation/11/respond/")
    print("5. Provider chooses method and submits estimate")
    print("6. Status updates automatically")
    print("7. Homeowner receives notification")

def main():
    # Resend WhatsApp to providers
    quotation = resend_whatsapp_quotation_11()
    
    if quotation:
        # Check current responses
        check_provider_responses()
        
        # Show expected flow
        show_expected_flow()
        
        print(f"\n=== Resend Complete ===")
        print(f"WhatsApp messages resent to providers for quotation 11")
        print(f"Providers can now respond with '1' or 'RESPOND 11'")
        print(f"Monitor: http://127.0.0.1:8000/gigs/quotation/11/")

if __name__ == "__main__":
    main()
