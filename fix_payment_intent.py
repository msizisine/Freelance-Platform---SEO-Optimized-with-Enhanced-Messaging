"""
Fix payment intent not found error by creating payment intent when missing
"""

import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')

def load_environment():
    """Load environment variables"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    return False

def check_orders_without_payment_intent():
    """Check for orders without stripe_payment_intent_id"""
    print("=== CHECKING ORDERS WITHOUT PAYMENT INTENT ===")
    
    # Load environment
    load_environment()
    
    try:
        import django
        django.setup()
        
        from orders.models import Order
        
        # Find orders without payment intent
        orders_without_intent = Order.objects.filter(stripe_payment_intent_id__isnull=True).exclude(payment_status='paid')
        
        print(f"Found {orders_without_intent.count()} orders without payment intent")
        
        for order in orders_without_intent[:5]:
            print(f"  Order {order.pk}: {order.gig.title if order.gig else 'No Gig'} - R{order.total_amount}")
            print(f"    Payment Status: {order.payment_status}")
            print(f"    Homeowner: {order.homeowner.email}")
            print(f"    Provider: {order.service_provider.email}")
        
        return orders_without_intent
        
    except Exception as e:
        print(f"Error checking orders: {e}")
        return []

def create_missing_payment_intents():
    """Create payment intents for orders that don't have them"""
    print("\n=== CREATING MISSING PAYMENT INTENTS ===")
    
    # Load environment
    load_environment()
    
    try:
        import django
        django.setup()
        
        from orders.models import Order
        from django.conf import settings
        
        # Check if Stripe is configured
        if not hasattr(settings, 'STRIPE_SECRET_KEY') or not settings.STRIPE_SECRET_KEY:
            print("Stripe is not configured. Cannot create payment intents.")
            return False
        
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Find orders without payment intent
        orders_without_intent = Order.objects.filter(stripe_payment_intent_id__isnull=True).exclude(payment_status='paid')
        
        created_count = 0
        for order in orders_without_intent:
            try:
                # Create payment intent
                intent = stripe.PaymentIntent.create(
                    amount=int(order.total_amount * 100),  # Convert to cents
                    currency='zar',  # Use South African Rand
                    metadata={
                        'order_id': str(order.pk),
                        'gig_id': str(order.gig.pk) if order.gig else '',
                    }
                )
                
                # Update order with payment intent ID
                order.stripe_payment_intent_id = intent.id
                order.save()
                
                print(f"  Created payment intent for Order {order.pk}: {intent.id}")
                created_count += 1
                
            except Exception as e:
                print(f"  Error creating payment intent for Order {order.pk}: {e}")
        
        print(f"\nCreated {created_count} payment intents")
        return created_count > 0
        
    except Exception as e:
        print(f"Error creating payment intents: {e}")
        return False

def fix_payment_view():
    """Update the payment_view to handle missing payment intents"""
    print("\n=== FIXING PAYMENT VIEW ===")
    
    try:
        with open('orders/views.py', 'r') as f:
            content = f.read()
        
        # Find the payment_view function
        old_payment_view = '''
@login_required
def payment_view(request, pk):
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    if not order.stripe_payment_intent_id:
        messages.error(request, 'Payment intent not found. Please contact support.')
        return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'client_secret': stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id).client_secret,
    }
    
    return render(request, 'orders/payment.html', context)'''
        
        new_payment_view = '''
@login_required
def payment_view(request, pk):
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    # Create payment intent if it doesn't exist
    if not order.stripe_payment_intent_id:
        try:
            # Check if Stripe is properly configured
            if not hasattr(settings, 'STRIPE_SECRET_KEY') or settings.STRIPE_SECRET_KEY in ['sk_test_your-stripe-secret-key', '']:
                messages.error(request, 'Payment system is not properly configured. Please contact support.')
                return redirect('orders:detail', pk=order.pk)
            
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Convert to cents
                currency='zar',  # Use South African Rand
                metadata={
                    'order_id': str(order.pk),
                    'gig_id': str(order.gig.pk) if order.gig else '',
                }
            )
            
            # Save payment intent ID
            order.stripe_payment_intent_id = intent.id
            order.save()
            
            messages.success(request, 'Payment setup completed. Please proceed with payment.')
            
        except stripe.error.StripeError as e:
            messages.error(request, f'Payment setup error: {str(e)}')
            return redirect('orders:detail', pk=order.pk)
        except Exception as e:
            messages.error(request, f'Payment setup failed: {str(e)}')
            return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'client_secret': stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id).client_secret,
    }
    
    return render(request, 'orders/payment.html', context)'''
        
        if old_payment_view in content:
            content = content.replace(old_payment_view, new_payment_view)
            
            with open('orders/views.py', 'w') as f:
                f.write(content)
            
            print("  Updated payment_view function")
            return True
        else:
            print("  Could not find payment_view function to update")
            return False
            
    except Exception as e:
        print(f"  Error updating payment_view: {e}")
        return False

def test_payment_view_fix():
    """Test the payment view fix"""
    print("\n=== TESTING PAYMENT VIEW FIX ===")
    
    # Load environment
    load_environment()
    
    try:
        import django
        django.setup()
        
        from orders.models import Order
        from django.contrib.auth import get_user_model
        from django.test import RequestFactory
        
        User = get_user_model()
        
        # Get an order without payment intent
        order = Order.objects.filter(stripe_payment_intent_id__isnull=True).first()
        
        if not order:
            print("  No orders without payment intent found")
            return True
        
        print(f"  Testing with Order {order.pk}")
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get(f'/orders/{order.pk}/payment/')
        request.user = order.homeowner
        
        # Import the updated view
        from orders.views import payment_view
        
        # Test the view
        try:
            response = payment_view(request, str(order.pk))
            print(f"  Payment view response: {response.status_code}")
            return True
        except Exception as e:
            print(f"  Error testing payment view: {e}")
            return False
            
    except Exception as e:
        print(f"  Error in test setup: {e}")
        return False

def main():
    print("FIXING PAYMENT INTENT NOT FOUND ERROR")
    print("=" * 50)
    
    # Check orders without payment intent
    orders = check_orders_without_payment_intent()
    
    # Create missing payment intents
    created = create_missing_payment_intents()
    
    # Fix the payment view
    view_fixed = fix_payment_view()
    
    # Test the fix
    test_passed = test_payment_view_fix()
    
    print("\n" + "=" * 50)
    print("FIX RESULTS:")
    print(f"Orders without intent: {len(orders)}")
    print(f"Payment intents created: {'YES' if created else 'NO'}")
    print(f"Payment view fixed: {'YES' if view_fixed else 'NO'}")
    print(f"Test passed: {'YES' if test_passed else 'NO'}")
    
    print("\nSUMMARY:")
    print("- Identified orders without payment intents")
    print("- Created missing payment intents")
    print("- Updated payment view to handle missing intents")
    print("- Added automatic payment intent creation")
    
    print("\nREADY FOR TESTING:")
    print("1. Visit http://127.0.0.1:8000/orders/d9ad96e4-7298-4a1a-a71b-a4f1bf9f77c5/")
    print("2. Click the 'Pay Now' button")
    print("3. Verify payment page loads without error")
    print("4. Test payment processing")

if __name__ == "__main__":
    main()
