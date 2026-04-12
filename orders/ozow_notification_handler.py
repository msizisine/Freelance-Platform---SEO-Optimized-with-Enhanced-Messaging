from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Order
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

def verify_ozow_hash(notification_data):
    """
    Verify the HashCheck value in Ozow notification
    """
    try:
        # Extract the received hash
        received_hash = notification_data.get('HashCheck', '')
        if not received_hash:
            logger.error("No HashCheck found in Ozow notification")
            return False
        
        # Create a copy of data without HashCheck, preserving original order
        data_for_hash = {k: v for k, v in notification_data.items() if k != 'HashCheck'}
        
        # Create the hash string using VALUES only (not key=value pairs)
        values_only = ''.join([str(value) for key, value in data_for_hash.items()])
        
        # Append secret key and convert to lowercase
        secret_key = getattr(settings, 'OZOW_API_SECRET', 'production-secret')
        hash_string = (values_only + secret_key).lower()
        
        # Generate SHA512 hash
        calculated_hash = hashlib.sha512(hash_string.encode()).hexdigest()
        
        logger.info(f"Ozow hash verification - Received: {received_hash}")
        logger.info(f"Ozow hash verification - Calculated: {calculated_hash}")
        
        return received_hash == calculated_hash
        
    except Exception as e:
        logger.error(f"Error verifying Ozow hash: {str(e)}")
        return False

@csrf_exempt
@require_POST
def ozow_notification_handler(request):
    """
    Handle Ozow TransactionNotificationResponse webhook notifications
    """
    try:
        # Parse the JSON notification from Ozow
        notification_data = json.loads(request.body)
        
        logger.info(f"Received Ozow notification: {notification_data}")
        
        # Verify the hash first
        if not verify_ozow_hash(notification_data):
            logger.error("Ozow HashCheck verification failed")
            return JsonResponse({'status': 'error', 'message': 'HashCheck verification failed'}, status=400)
        
        logger.info(f"Received Ozow notification: {notification_data}")
        
        # Extract key information from notification
        transaction_id = notification_data.get('id')
        status = notification_data.get('status', 'Unknown')
        amount = notification_data.get('amount')
        transaction_reference = notification_data.get('transactionReference')
        
        # Find the order by transaction ID or reference
        order = None
        if transaction_id:
            order = Order.objects.filter(ozow_transaction_id=transaction_id).first()
        elif transaction_reference:
            order = Order.objects.filter(order_number=transaction_reference).first()
        
        if order:
            # Update order based on notification status
            if status == 'Complete':
                order.payment_status = 'paid'
                order.paid_amount = amount
                order.save()
                logger.info(f"Order {order.order_number} marked as paid. Amount: {amount}")
            elif status == 'Failed':
                order.payment_status = 'failed'
                order.save()
                logger.warning(f"Order {order.order_number} payment failed. Amount: {amount}")
            else:
                # Other statuses (Pending, Processing, etc.)
                logger.info(f"Order {order.order_number} status updated to: {status}")
            
            return JsonResponse({'status': 'success'})
        else:
            logger.error("No order found for Ozow notification")
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=404)
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Ozow notification: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing Ozow notification: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Processing error'}, status=500)
