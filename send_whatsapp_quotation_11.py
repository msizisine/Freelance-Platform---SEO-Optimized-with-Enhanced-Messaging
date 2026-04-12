"""
Send WhatsApp message to service provider for quotation 11
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

def send_whatsapp_to_quotation_11():
    """Send interactive WhatsApp message to providers for quotation 11"""
    print("=== Sending WhatsApp for Quotation 11 ===")
    
    try:
        # Get quotation 11
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
                print("Sending interactive WhatsApp message...")
                
                result = flow.send_interactive_quotation_request(
                    to=provider.phone,
                    quotation=quotation,
                    provider=provider
                )
                
                print(f"Result: {result.get('success')}")
                print(f"Message ID: {result.get('message_id')}")
                print(f"Service Used: {result.get('service_used')}")
                
                if result.get('success'):
                    print("WhatsApp sent successfully!")
                    print("Provider can now reply with: RESPOND 11")
                else:
                    print(f"Error: {result.get('error')}")
                    print("This might be due to rate limiting (1 message/minute on free trial)")
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

To respond, reply with:
RESPOND {quotation.pk} - to provide your estimate
IGNORE {quotation.pk} - to decline this request

Example: RESPOND {quotation.pk}

This is an automated message from Freelance Platform."""
        
        print("Message that was/will be sent:")
        print("-" * 50)
        print(message)
        print("-" * 50)
        
        return quotation
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")
        return None

def check_provider_responses():
    """Check if any providers have responded to quotation 11"""
    print("\n=== Checking Provider Responses ===")
    
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
            else:
                print("Method: Dashboard response")
        
        if responses.count() == 0:
            print("No responses yet - providers should be receiving WhatsApp now!")
        
    except QuotationRequest.DoesNotExist:
        print("Quotation 11 not found")

def show_next_steps():
    """Show what happens next after WhatsApp is sent"""
    print("\n=== Next Steps ===")
    print("1. Providers receive WhatsApp message with RESPOND/IGNORE options")
    print("2. Provider replies: RESPOND 11")
    print("3. System asks for estimate details")
    print("4. Provider replies: ESTIMATE 11 5000 3_days")
    print("5. Estimate is saved and homeowner is notified")
    print("6. Status automatically updates to 'evaluation_period'")
    print("7. Homeowner can ACCEPT/REJECT via WhatsApp or dashboard")
    print("8. Private job is created when estimate is accepted")

def main():
    # Send WhatsApp to providers
    quotation = send_whatsapp_to_quotation_11()
    
    if quotation:
        # Check current responses
        check_provider_responses()
        
        # Show next steps
        show_next_steps()
        
        print(f"\n=== Summary ===")
        print(f"WhatsApp messages sent to providers for quotation 11")
        print(f"Providers can now respond via WhatsApp commands")
        print(f"Status will update automatically when responses are received")
        print(f"Check http://127.0.0.1:8000/gigs/quotation/11/ for live updates")

if __name__ == "__main__":
    main()
