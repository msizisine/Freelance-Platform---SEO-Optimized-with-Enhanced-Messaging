"""
Views for Quote Request System with WhatsApp Integration
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Gig, Category
from .models_quote import QuoteRequest, QuoteResponse, WhatsAppInteraction
from notifications.services import NotificationService

# Try to import WhatsApp flows (optional module)
try:
    from .whatsapp_flows import WhatsAppFlowManager
except ImportError:
    WhatsAppFlowManager = None


@login_required
def request_quote_via_whatsapp(request, gig_id):
    """Initiate quote request via WhatsApp Flow"""
    gig = get_object_or_404(Gig, id=gig_id)
    
    if request.user.user_type != 'homeowner':
        messages.error(request, "Only homeowners can request quotes.")
        return redirect('gigs:detail', pk=gig_id)
    
    try:
        # Create quote request
        quote_request = QuoteRequest.objects.create(
            homeowner=request.user,
            service_provider=gig.user,
            title=gig.title,
            service_category=gig.category.name if gig.category else 'General',
            location=request.user.profile.location or 'To be provided',
            expires_at=timezone.now() + timezone.timedelta(days=7),
            whatsapp_flow_id=f"quote_request_{gig.id}"
        )
        
        # Send WhatsApp Flow to homeowner
        if request.user.phone and WhatsAppFlowManager:
            result = WhatsAppFlowManager.send_quote_request_flow(
                request.user.phone,
                str(quote_request.id),
                {'gig_title': gig.title, 'provider_name': gig.user.get_full_name()}
            )
            
            messages.success(request, "Quote request initiated! Check your WhatsApp for the form.")
        elif not WhatsAppFlowManager:
            messages.warning(request, "WhatsApp integration is not available. Quote request created without WhatsApp notification.")
        else:
            messages.warning(request, "Please add your phone number to your profile to use WhatsApp quote requests.")
        
        return redirect('gigs:quotes_list')
        
    except Exception as e:
        messages.error(request, f"Error creating quote request: {str(e)}")
        return redirect('gigs:detail', pk=gig_id)
