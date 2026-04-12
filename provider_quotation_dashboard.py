"""
Provider Quotation Dashboard
Shows providers their WhatsApp responses and quotation status
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
from gigs.models import QuotationRequest, QuotationResponse, QuotationRequestProvider
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

def get_provider_quotation_dashboard(provider_email: str):
    """Get comprehensive quotation dashboard for a provider"""
    print(f"=== Quotation Dashboard for {provider_email} ===")
    
    try:
        provider = User.objects.get(email=provider_email, user_type='service_provider')
    except User.DoesNotExist:
        print(f"Provider {provider_email} not found")
        return
    
    # Get all quotations sent to this provider
    sent_quotations = QuotationRequestProvider.objects.filter(
        service_provider=provider
    ).select_related('quotation_request', 'quotation_request__homeowner', 'quotation_request__category')
    
    print(f"\nTotal quotations sent: {sent_quotations.count()}")
    
    # Group by status
    status_groups = {
        'pending': [],
        'responding': [],
        'submitted': [],
        'accepted': [],
        'rejected': [],
        'declined': [],
        'expired': []
    }
    
    for sent_quotation in sent_quotations:
        quotation = sent_quotation.quotation_request
        response = QuotationResponse.objects.filter(
            quotation_request=quotation,
            service_provider=provider
        ).first()
        
        # Determine status
        if not response:
            if quotation.status == 'evaluation_period' or (quotation.response_deadline and quotation.is_response_deadline_passed()):
                status = 'expired'
            else:
                status = 'pending'
        elif response.status == 'pending':
            status = 'submitted'
        elif response.status == 'accepted':
            status = 'accepted'
        elif response.status == 'rejected':
            status = 'rejected'
        else:
            status = 'pending'
        
        # Check if it's a decline
        if response and response.estimated_price == 0 and response.estimated_duration == 'declined':
            status = 'declined'
        
        status_groups[status].append({
            'quotation': quotation,
            'response': response,
            'sent_at': sent_quotation.sent_at,
            'status': status,
            'whatsapp_used': response and "Submitted via WhatsApp" in response.notes,
            'whatsapp_declined': response and "Declined via WhatsApp" in response.price_breakdown
        })
    
    # Display statistics
    print("\n=== Response Statistics ===")
    for status, items in status_groups.items():
        if items:
            print(f"{status.title()}: {len(items)} quotations")
    
    # Display detailed breakdown
    for status, items in status_groups.items():
        if not items:
            continue
            
        print(f"\n=== {status.title()} Quotations ===")
        
        for item in items:
            quotation = item['quotation']
            response = item['response']
            
            print(f"\nQuotation {quotation.pk}: {quotation.title}")
            print(f"  Client: {quotation.homeowner.get_full_name() or quotation.homeowner.email}")
            print(f"  Category: {quotation.category.name}")
            print(f"  Budget: {quotation.budget_range}")
            print(f"  Location: {quotation.location}")
            print(f"  Sent: {item['sent_at'].strftime('%Y-%m-%d %H:%M')}")
            
            if response:
                print(f"  Response: {response.submitted_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"  Price: R{response.estimated_price}")
                print(f"  Duration: {response.estimated_duration}")
                print(f"  Status: {response.status}")
                
                if item['whatsapp_used']:
                    print(f"  <i class='fab fa-whatsapp text-success'></i> Submitted via WhatsApp")
                elif item['whatsapp_declined']:
                    print(f"  <i class='fab fa-whatsapp text-info'></i> Declined via WhatsApp")
                else:
                    print(f"  <i class='fas fa-laptop text-muted'></i> Submitted via dashboard")
            else:
                print(f"  Status: Not responded")
                
                # Show WhatsApp interaction status
                if provider.phone:
                    print(f"  <i class='fab fa-whatsapp text-primary'></i> WhatsApp available")
                    print(f"  Reply: RESPOND {quotation.pk} to start")
                else:
                    print(f"  <i class='fas fa-envelope text-warning'></i> Email only (no phone)")
            
            # Show deadline
            if quotation.response_deadline:
                if quotation.is_response_deadline_passed():
                    print(f"  <i class='fas fa-exclamation-triangle text-danger'></i> Deadline expired")
                else:
                    time_left = quotation.response_deadline - timezone.now()
                    days_left = time_left.days
                    hours_left = time_left.seconds // 3600
                    print(f"  <i class='fas fa-clock text-info'></i> {days_left}d {hours_left}h remaining")
            else:
                print(f"  <i class='fas fa-infinity text-muted'></i> No deadline set")

def show_whatsapp_interaction_summary():
    """Show summary of WhatsApp interactions for all providers"""
    print("\n=== WhatsApp Interaction Summary ===")
    
    providers = User.objects.filter(user_type='service_provider', phone__isnull=False)
    
    total_providers = providers.count()
    whatsapp_responses = 0
    whatsapp_declines = 0
    
    for provider in providers:
        # Get all responses for this provider
        responses = QuotationResponse.objects.filter(service_provider=provider)
        
        provider_whatsapp_responses = responses.filter(notes__contains='Submitted via WhatsApp').count()
        provider_whatsapp_declines = responses.filter(price_breakdown__contains='Declined via WhatsApp').count()
        
        whatsapp_responses += provider_whatsapp_responses
        whatsapp_declines += provider_whatsapp_declines
        
        if provider_whatsapp_responses > 0 or provider_whatsapp_declines > 0:
            print(f"\n{provider.get_full_name() or provider.email}:")
            print(f"  WhatsApp responses: {provider_whatsapp_responses}")
            print(f"  WhatsApp declines: {provider_whatsapp_declines}")
    
    print(f"\n=== Overall Statistics ===")
    print(f"Providers with WhatsApp: {total_providers}")
    print(f"Total WhatsApp responses: {whatsapp_responses}")
    print(f"Total WhatsApp declines: {whatsapp_declines}")
    print(f"WhatsApp interaction rate: {(whatsapp_responses + whatsapp_declines) / max(1, total_providers):.1f} per provider")

def show_recent_whatsapp_activity():
    """Show recent WhatsApp activity"""
    print("\n=== Recent WhatsApp Activity ===")
    
    # Get recent WhatsApp responses
    recent_responses = QuotationResponse.objects.filter(
        notes__contains='Submitted via WhatsApp'
    ).order_by('-submitted_at')[:5]
    
    if recent_responses:
        print("Recent WhatsApp submissions:")
        for response in recent_responses:
            print(f"  {response.submitted_at.strftime('%Y-%m-%d %H:%M')} - {response.service_provider.email}")
            print(f"    Quotation {response.quotation_request.pk}: R{response.estimated_price}")
    else:
        print("No recent WhatsApp responses found")
    
    # Get recent WhatsApp declines
    recent_declines = QuotationResponse.objects.filter(
        price_breakdown__contains='Declined via WhatsApp'
    ).order_by('-submitted_at')[:5]
    
    if recent_declines:
        print("\nRecent WhatsApp declines:")
        for response in recent_declines:
            print(f"  {response.submitted_at.strftime('%Y-%m-%d %H:%M')} - {response.service_provider.email}")
            print(f"    Quotation {response.quotation_request.pk}: {response.quotation_request.title}")

def main():
    # Show dashboard for sips mav
    get_provider_quotation_dashboard('msizi34@mobi-cafe.co.za')
    
    # Show WhatsApp interaction summary
    show_whatsapp_interaction_summary()
    
    # Show recent activity
    show_recent_whatsapp_activity()
    
    print("\n=== Dashboard Features ===")
    print("1. Shows all quotations sent to provider")
    print("2. Groups by response status (pending, submitted, accepted, etc.)")
    print("3. Indicates WhatsApp vs dashboard responses")
    print("4. Shows remaining time for pending quotations")
    print("5. Provides WhatsApp command reminders")
    print("6. Tracks WhatsApp interaction statistics")

if __name__ == "__main__":
    main()
