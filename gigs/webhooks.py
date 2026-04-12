"""
WhatsApp Webhooks for Meta Direct WhatsApp Business API
"""
import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from .models_quote import WhatsAppInteraction

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """Handle Meta Direct WhatsApp webhooks"""
    
    if request.method == "GET":
        # Webhook verification for Meta
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if (mode == 'subscribe' and 
            token == getattr(settings, 'WHATSAPP_WEBHOOK_VERIFICATION_TOKEN', '')):
            logger.info("WhatsApp webhook verified successfully")
            return HttpResponse(challenge)
        else:
            logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
            return HttpResponse("Verification failed", status=403)
    
    elif request.method == "POST":
        # Handle incoming WhatsApp messages
        try:
            data = json.loads(request.body)
            logger.info(f"Received WhatsApp webhook: {data}")
            
            # Process webhook data
            if 'entry' in data:
                for entry in data['entry']:
                    if 'changes' in entry:
                        for change in entry['changes']:
                            if 'messages' in change.get('value', {}):
                                messages = change['value']['messages']
                                for message in messages:
                                    process_incoming_message(message)
            
            return HttpResponse("OK", status=200)
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {str(e)}")
            return HttpResponse("Error", status=500)
    
    return HttpResponse("Method not allowed", status=405)

def process_incoming_message(message_data):
    """Process incoming WhatsApp message"""
    try:
        # Extract message details
        from_number = message_data.get('from')
        message_type = message_data.get('type')
        timestamp = message_data.get('timestamp')
        
        if message_type == 'text':
            text_body = message_data.get('text', {}).get('body', '')
            process_text_message(from_number, text_body, timestamp)
        
        elif message_type == 'interactive':
            interactive_type = message_data.get('interactive', {}).get('type')
            if interactive_type == 'flow':
                process_flow_response(message_data)
            elif interactive_type == 'button_reply':
                process_button_response(message_data)
        
        elif message_type == 'button':
            process_button_response(message_data)
        
        # Log the interaction
        WhatsAppInteraction.objects.create(
            phone_number=from_number,
            interaction_type='incoming_message',
            processing_status='received',
            payload=message_data
        )
        
        logger.info(f"Processed incoming message from {from_number}")
        
    except Exception as e:
        logger.error(f"Error processing incoming message: {str(e)}")

def process_text_message(from_number, text_body, timestamp):
    """Process incoming text message"""
    try:
        # Handle text responses
        text_body = text_body.lower().strip()
        
        # Check for quote responses
        if any(keyword in text_body for keyword in ['accept', 'interested', 'yes', 'quote']):
            handle_quote_acceptance(from_number, text_body)
        elif any(keyword in text_body for keyword in ['decline', 'no', 'not interested']):
            handle_quote_decline(from_number, text_body)
        elif any(keyword in text_body for keyword in ['price', 'cost', 'how much']):
            handle_price_inquiry(from_number, text_body)
        else:
            handle_general_inquiry(from_number, text_body)
            
    except Exception as e:
        logger.error(f"Error processing text message: {str(e)}")

def process_flow_response(message_data):
    """Process WhatsApp Flow response"""
    try:
        from_number = message_data.get('from')
        flow_response = message_data.get('interactive', {}).get('flow', {})
        flow_token = flow_response.get('flow_token')
        flow_data = flow_response.get('response', {})
        
        # Extract flow token to identify the context
        if flow_token:
            if 'provider_response' in flow_token:
                handle_provider_flow_response(from_number, flow_data)
            elif 'homeowner_decision' in flow_token:
                handle_homeowner_flow_response(from_number, flow_data)
            elif 'quote_request' in flow_token:
                handle_quote_request_flow(from_number, flow_data)
        
        logger.info(f"Processed flow response from {from_number}")
        
    except Exception as e:
        logger.error(f"Error processing flow response: {str(e)}")

def process_button_response(message_data):
    """Process button response"""
    try:
        from_number = message_data.get('from')
        button_reply = message_data.get('interactive', {}).get('button_reply', {})
        button_id = button_reply.get('id')
        button_text = button_reply.get('title')
        
        # Handle button responses
        if 'accept' in button_id.lower():
            handle_quote_acceptance(from_number, f"Button: {button_text}")
        elif 'decline' in button_id.lower():
            handle_quote_decline(from_number, f"Button: {button_text}")
        elif 'more_info' in button_id.lower():
            handle_more_info_request(from_number, f"Button: {button_text}")
        
        logger.info(f"Processed button response from {from_number}: {button_text}")
        
    except Exception as e:
        logger.error(f"Error processing button response: {str(e)}")

def handle_provider_flow_response(from_number, flow_data):
    """Handle provider flow response (quote acceptance/decline)"""
    try:
        from gigs.models_quote import QuoteRequest, QuoteResponse
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Find provider by phone number
        provider = User.objects.filter(phone=from_number, user_type='service_provider').first()
        if not provider:
            logger.warning(f"Provider not found for phone: {from_number}")
            return
        
        # Extract quote request ID from flow data
        quote_request_id = flow_data.get('quote_request_id')
        if not quote_request_id:
            logger.warning("No quote request ID in flow response")
            return
        
        # Get quote request
        quote_request = QuoteRequest.objects.filter(id=quote_request_id).first()
        if not quote_request:
            logger.warning(f"Quote request not found: {quote_request_id}")
            return
        
        # Extract response data
        response_type = flow_data.get('response_type')
        quoted_price = flow_data.get('quoted_price')
        availability = flow_data.get('availability')
        notes = flow_data.get('notes')
        
        # Create quote response
        quote_response = QuoteResponse.objects.create(
            quote_request=quote_request,
            service_provider=provider,
            response_type=response_type,
            estimated_price=quoted_price,
            message=f"Availability: {availability}\n\nNotes: {notes}",
            price_description=f"Availability: {availability}",
            created_at=timezone.now()
        )
        
        # Update quote request status
        if response_type == 'accept':
            quote_request.status = 'provider_responded'
        else:
            quote_request.status = 'provider_declined'
        quote_request.save()
        
        # Notify homeowner
        from .whatsapp_flows import WhatsAppFlowManager
        WhatsAppFlowManager.notify_homeowner_of_provider_response(
            quote_request.homeowner.phone,
            str(quote_request.id),
            provider.get_full_name() or provider.email,
            {
                'response_type': response_type,
                'quoted_price': quoted_price,
                'availability': availability,
                'notes': notes
            }
        )
        
        logger.info(f"Provider response processed: {quote_request.id} by {provider.email}")
        
    except Exception as e:
        logger.error(f"Error handling provider flow response: {str(e)}")

def handle_homeowner_flow_response(from_number, flow_data):
    """Handle homeowner flow response (accept/reject quote)"""
    try:
        from gigs.models_quote import QuoteRequest, QuoteResponse
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Find homeowner by phone number
        homeowner = User.objects.filter(phone=from_number, user_type='homeowner').first()
        if not homeowner:
            logger.warning(f"Homeowner not found for phone: {from_number}")
            return
        
        # Extract quote request ID
        quote_request_id = flow_data.get('quote_request_id')
        if not quote_request_id:
            logger.warning("No quote request ID in flow response")
            return
        
        # Get quote request
        quote_request = QuoteRequest.objects.filter(id=quote_request_id).first()
        if not quote_request:
            logger.warning(f"Quote request not found: {quote_request_id}")
            return
        
        # Get the latest response
        quote_response = quote_request.responses.latest('created_at')
        
        # Extract decision
        decision = flow_data.get('decision')
        feedback = flow_data.get('feedback', '')
        
        # Update quote response
        if decision == 'accept':
            quote_response.is_accepted = True
            quote_request.status = 'accepted'
        elif decision == 'reject':
            quote_response.is_accepted = False
            quote_request.status = 'rejected'
        elif decision == 'negotiate':
            quote_response.is_accepted = False
            quote_request.status = 'negotiation'
        
        # Add feedback
        if feedback:
            quote_response.message += f"\n\nHomeowner Feedback: {feedback}"
        
        quote_response.save()
        quote_request.save()
        
        # Notify provider
        from .whatsapp_flows import WhatsAppFlowManager
        WhatsAppFlowManager.notify_provider_of_homeowner_decision(
            quote_request.service_provider.phone,
            str(quote_request.id),
            decision,
            feedback
        )
        
        # Create job if accepted
        if decision == 'accept':
            WhatsAppFlowManager.create_job_from_accepted_quote(quote_request, quote_response)
        
        logger.info(f"Homeowner decision processed: {quote_request.id} - {decision}")
        
    except Exception as e:
        logger.error(f"Error handling homeowner flow response: {str(e)}")

def handle_quote_acceptance(from_number, message):
    """Handle simple quote acceptance via text"""
    # This would be used for simple text responses when flows aren't available
    pass

def handle_quote_decline(from_number, message):
    """Handle simple quote decline via text"""
    # This would be used for simple text responses when flows aren't available
    pass

def handle_price_inquiry(from_number, message):
    """Handle price inquiry"""
    # Send automated price information
    pass

def handle_general_inquiry(from_number, message):
    """Handle general inquiry"""
    # Send automated response or route to support
    pass

def handle_more_info_request(from_number, message):
    """Handle request for more information"""
    # Send additional details about the quote request
    pass

def handle_quote_request_flow(from_number, flow_data):
    """Handle new quote request flow"""
    # Process new quote request submitted via WhatsApp flow
    pass
