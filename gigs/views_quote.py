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
            
        return redirect('gigs:quote_request_detail', pk=quote_request.id)
        
    except Exception as e:
        messages.error(request, f"Error initiating quote request: {str(e)}")
        return redirect('gigs:detail', pk=gig_id)


class QuoteRequestListView(LoginRequiredMixin, ListView):
    """List of quote requests for the current user"""
    model = QuoteRequest
    template_name = 'gigs/quote_request_list.html'
    context_object_name = 'quote_requests'
    paginate_by = 10
    
    def get_queryset(self):
        if self.request.user.user_type == 'homeowner':
            return QuoteRequest.objects.filter(homeowner=self.request.user)
        else:
            return QuoteRequest.objects.filter(service_provider=self.request.user)


class QuoteRequestDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a quote request"""
    model = QuoteRequest
    template_name = 'gigs/quote_request_detail.html'
    context_object_name = 'quote_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote_request = self.get_object()
        
        # Check if user can view this request
        if (self.request.user != quote_request.homeowner and 
            self.request.user != quote_request.service_provider):
            raise PermissionError("You don't have permission to view this quote request.")
        
        # Add responses
        context['responses'] = quote_request.responses.all()
        context['can_respond'] = (
            self.request.user == quote_request.service_provider and 
            quote_request.status == 'pending' and 
            not quote_request.is_expired()
        )
        
        return context


class QuoteResponseCreateView(LoginRequiredMixin, CreateView):
    """Create a quote response (web alternative to WhatsApp)"""
    model = QuoteResponse
    template_name = 'gigs/quote_response_form.html'
    fields = ['response_type', 'estimated_price', 'price_description', 
              'estimated_days', 'start_date', 'message']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote_request_id = self.kwargs['quote_request_id']
        context['quote_request'] = get_object_or_404(QuoteRequest, id=quote_request_id)
        return context
    
    def form_valid(self, form):
        quote_request_id = self.kwargs['quote_request_id']
        quote_request = get_object_or_404(QuoteRequest, id=quote_request_id)
        
        # Check permissions
        if self.request.user != quote_request.service_provider:
            form.add_error(None, "You can only respond to your own quote requests.")
            return self.form_invalid(form)
        
        if quote_request.status != 'pending' or quote_request.is_expired():
            form.add_error(None, "This quote request is no longer accepting responses.")
            return self.form_invalid(form)
        
        form.instance.quote_request = quote_request
        form.instance.service_provider = self.request.user
        
        response = super().form_valid(form)
        
        # Mark quote request as responded
        quote_request.mark_as_responded()
        
        # Notify homeowner
        NotificationService.send_notification(
            recipient=quote_request.homeowner,
            notification_type='quotation_received',
            title=f'New Quote Response: {quote_request.title}',
            message=f'{self.request.user.get_full_name()} has responded to your quote request.',
            gig=None,
            order=None,
            channels=['in_app', 'email']
        )
        
        messages.success(self.request, "Your quote response has been sent!")
        return response
    
    def get_success_url(self):
        return reverse_lazy('gigs:quote_request_detail', kwargs={'pk': self.kwargs['quote_request_id']})


@csrf_exempt
def whatsapp_webhook(request):
    """Handle WhatsApp webhook for flows and messages"""
    if request.method == 'GET':
        # WhatsApp verification
        challenge = request.GET.get('hub.challenge')
        if challenge:
            return HttpResponse(challenge)
        return HttpResponse('OK')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Handle different webhook types
            if 'messages' in data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}):
                return _handle_message_webhook(data)
            elif 'flows' in data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}):
                return _handle_flow_webhook(data)
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'ok'})


def _handle_message_webhook(data):
    """Handle incoming WhatsApp messages"""
    try:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        phone_number = message_data['from']
        
        # Handle text responses (for simple interactions)
        if 'text' in message_data:
            message_text = message_data['text']['body'].strip().upper()
            
            # Handle simple responses like "ACCEPT", "DECLINE"
            if message_text in ['ACCEPT', 'DECLINE', 'YES', 'NO']:
                return _handle_simple_response(phone_number, message_text)
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def _handle_flow_webhook(data):
    """Handle WhatsApp Flow responses"""
    try:
        flow_data = data['entry'][0]['changes'][0]['value']['flows'][0]
        
        # Process flow response
        if WhatsAppFlowManager:
            result = WhatsAppFlowManager.handle_flow_response(flow_data)
            return JsonResponse(result)
        else:
            return JsonResponse({'status': 'error', 'message': 'WhatsApp flows not available'}, status=503)
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def _handle_simple_response(phone_number, message_text):
    """Handle simple text responses"""
    try:
        from django.contrib.auth import get_user_model
        from notifications.services import NotificationService
        
        User = get_user_model()
        
        # Find user by phone number
        try:
            user = User.objects.get(phone=phone_number)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'})
        
        # Handle different response types
        if message_text in ['ACCEPT', 'YES']:
            # Look for recent job offers or quote requests
            recent_quote = QuoteRequest.objects.filter(
                service_provider=user,
                status='pending'
            ).order_by('-created_at').first()
            
            if recent_quote:
                # Create acceptance response
                QuoteResponse.objects.create(
                    quote_request=recent_quote,
                    service_provider=user,
                    response_type='accepted',
                    message="Accepted via WhatsApp",
                    whatsapp_flow_response={'response_type': 'accepted', 'via': 'whatsapp_text'}
                )
                
                # Notify homeowner
                NotificationService.send_notification(
                    recipient=recent_quote.homeowner,
                    notification_type='quotation_accepted',
                    title='Quote Accepted!',
                    message=f'{user.get_full_name()} has accepted your quote request.',
                    channels=['in_app', 'email', 'whatsapp']
                )
                
                return JsonResponse({'status': 'success', 'message': 'Quote accepted'})
        
        elif message_text in ['DECLINE', 'NO']:
            # Handle decline
            recent_quote = QuoteRequest.objects.filter(
                service_provider=user,
                status='pending'
            ).order_by('-created_at').first()
            
            if recent_quote:
                QuoteResponse.objects.create(
                    quote_request=recent_quote,
                    service_provider=user,
                    response_type='declined',
                    message="Declined via WhatsApp",
                    whatsapp_flow_response={'response_type': 'declined', 'via': 'whatsapp_text'}
                )
                
                return JsonResponse({'status': 'success', 'message': 'Quote declined'})
        
        return JsonResponse({'status': 'ok', 'message': 'Response processed'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def resend_quote_request_whatsapp(request, quote_request_id):
    """Resend quote request via WhatsApp"""
    quote_request = get_object_or_404(QuoteRequest, id=quote_request_id)
    
    if request.user != quote_request.homeowner:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    try:
        if request.user.phone and WhatsAppFlowManager:
            result = WhatsAppFlowManager.send_quote_request_flow(
                request.user.phone,
                str(quote_request.id),
                {'resend': True}
            )
            
            return JsonResponse({'status': 'success', 'message': 'Quote request sent via WhatsApp'})
        elif not WhatsAppFlowManager:
            return JsonResponse({'status': 'error', 'message': 'WhatsApp integration not available'}, status=503)
        else:
            return JsonResponse({'status': 'error', 'message': 'No phone number on file'}, status=400)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@login_required
@require_POST
def accept_quote_response(request, response_id):
    """Accept a quote response"""
    quote_response = get_object_or_404(QuoteResponse, id=response_id)
    quote_request = quote_response.quote_request
    
    # Check permissions
    if request.user != quote_request.homeowner:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    if quote_response.response_type != 'quote':
        return JsonResponse({'status': 'error', 'message': 'Cannot accept non-quote response'}, status=400)
    
    try:
        # Mark response as accepted
        quote_response.is_accepted = True
        quote_response.save()
        
        # Update quote request status
        quote_request.status = 'accepted'
        quote_request.save()
        
        # Notify service provider
        NotificationService.send_notification(
            recipient=quote_response.service_provider,
            notification_type='quotation_accepted',
            title='Quote Accepted!',
            message=f'{request.user.get_full_name()} has accepted your quote for {quote_request.title}.',
            gig=None,
            order=None,
            channels=['in_app', 'email', 'whatsapp']
        )
        
        # Create order from accepted quote
        from orders.models import Order
        order = Order.objects.create(
            gig=None,  # This is a custom quote, not tied to a gig
            client=request.user,
            service_provider=quote_response.service_provider,
            title=quote_request.title,
            description=quote_request.description,
            price=quote_response.estimated_price,
            status='pending_payment',
            quote_request=quote_request,
            quote_response=quote_response
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Quote accepted successfully!',
            'order_id': order.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@login_required
@require_POST
def request_quote_via_whatsapp_bulk(request):
    """Handle bulk WhatsApp quote requests for multiple providers"""
    if request.user.user_type != 'homeowner':
        return JsonResponse({'status': 'error', 'message': 'Only homeowners can request quotes'}, status=403)
    
    if not request.user.phone:
        return JsonResponse({'status': 'error', 'message': 'Please add your phone number to use WhatsApp quote requests'}, status=400)
    
    try:
        import json
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'description', 'category', 'location', 'providers']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({'status': 'error', 'message': f'Missing required field: {field}'}, status=400)
        
        from gigs.models_quote import QuoteRequest
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Get selected providers
        provider_ids = data.get('providers', [])
        if isinstance(provider_ids, str):
            provider_ids = [provider_ids]
        
        providers = User.objects.filter(id__in=provider_ids, user_type='service_provider')
        if not providers.exists():
            return JsonResponse({'status': 'error', 'message': 'No valid service providers selected'}, status=400)
        
        # Create quote requests for each provider
        quote_requests = []
        for provider in providers:
            quote_request = QuoteRequest.objects.create(
                homeowner=request.user,
                service_provider=provider,
                title=data['title'],
                description=data['description'],
                service_category=data['category'],
                location=data['location'],
                preferred_date=data.get('start_date') or None,
                budget_range=data.get('budget_range', ''),
                priority=data.get('urgency', 'medium'),
                expires_at=timezone.now() + timezone.timedelta(days=7),
                whatsapp_flow_id=f"quote_request_bulk_{request.user.id}_{timezone.now().timestamp()}"
            )
            quote_requests.append(quote_request)
        
        # Send WhatsApp Flow to homeowner
        try:
            if WhatsAppFlowManager:
                # Send to first quote request as representative
                result = WhatsAppFlowManager.send_quote_request_flow(
                    request.user.phone,
                    str(quote_requests[0].id),
                    {
                        'bulk_request': True,
                        'provider_count': len(providers),
                        'providers': [p.get_full_name() or p.email for p in providers]
                    }
                )
                
                # Notify service providers
                for quote_request in quote_requests:
                    WhatsAppFlowManager._notify_service_providers(quote_request)
                
                return JsonResponse({
                    'status': 'success', 
                    'message': f'Quote requests sent to {len(providers)} providers via WhatsApp!',
                    'redirect_url': f'/gigs/quotes/list/'
                })
            else:
                return JsonResponse({
                    'status': 'success', 
                    'message': f'Quote requests created for {len(providers)} providers. WhatsApp integration not available.',
                    'redirect_url': f'/gigs/quotes/list/'
                })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'WhatsApp error: {str(e)}'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def quote_analytics(request):
    """Analytics for quote requests and responses"""
    if request.user.user_type == 'homeowner':
        quote_requests = QuoteRequest.objects.filter(homeowner=request.user)
        context = {
            'total_requests': quote_requests.count(),
            'pending_requests': quote_requests.filter(status='pending').count(),
            'responded_requests': quote_requests.filter(status='responded').count(),
            'accepted_requests': quote_requests.filter(responses__response_type='accepted').count(),
            'recent_requests': quote_requests.order_by('-created_at')[:5]
        }
    else:
        quote_requests = QuoteRequest.objects.filter(service_provider=request.user)
        responses = QuoteResponse.objects.filter(service_provider=request.user)
        context = {
            'total_received': quote_requests.count(),
            'pending_responses': quote_requests.filter(status='pending').count(),
            'total_responses': responses.count(),
            'accepted_quotes': responses.filter(response_type='accepted').count(),
            'recent_responses': responses.order_by('-created_at')[:5]
        }
    
    return render(request, 'gigs/quote_analytics.html', context)
