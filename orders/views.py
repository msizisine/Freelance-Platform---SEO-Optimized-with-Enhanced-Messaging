from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Sum
from django.conf import settings
# import stripe  # Import bank details models
from core.models_config import BankAccount
from .models import OrderFile, OrderRevision, OrderDispute
from .models_bank import EFTPaymentConfirmation
from .forms import OrderForm, OrderMessageForm, OrderRevisionForm, JobCreationForm
from gigs.models import Gig, GigPackage
from django.contrib.auth import get_user_model

# Import the new view function
from .create_order_from_provider import create_order_from_provider
from .create_private_job import create_private_job
from . import job_offer_views
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Order
import json
import logging
import requests
import urllib.parse
import hashlib

logger = logging.getLogger(__name__)

# Import the new view function
from .ozow_notification_handler import ozow_notification_handler


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'service_provider':
            return Order.objects.filter(service_provider=user)
        else:
            return Order.objects.filter(homeowner=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(Q(homeowner=user) | Q(service_provider=user))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['order_messages'] = order.messages.all()
        context['files'] = order.delivery_files.all()
        context['revisions'] = order.revisions.all()
        context['message_form'] = OrderMessageForm()
        
        if order.status == 'revision_requested':
            context['revision_form'] = OrderRevisionForm()
        
        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_create.html'
    
    def get_form_class(self):
        """Use JobCreationForm for new job creation, OrderForm for gig-based orders"""
        gig_id = self.kwargs.get('gig_id')
        if gig_id:
            return OrderForm
        else:
            return JobCreationForm
    
    def get_success_url(self):
        return reverse_lazy('orders:payment', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gig_id = self.kwargs.get('gig_id')
        if gig_id:
            gig = get_object_or_404(Gig, pk=gig_id)
            context['gig'] = gig
        return context
    
    def form_valid(self, form):
        form.instance.homeowner = self.request.user
        
        # Check if this is JobCreationForm (new job) or OrderForm (gig-based)
        if isinstance(form, JobCreationForm):
            # This is a new job creation - create a gig from form data only, no order
            from gigs.models import Gig, Category
            
            # Get or create category
            category_name = form.cleaned_data.get('category', 'General')
            category, created = Category.objects.get_or_create(name=category_name)
            
            # Create a new gig from form data
            gig = Gig.objects.create(
                title=form.cleaned_data.get('job_title', 'New Job'),
                description=form.cleaned_data.get('description', ''),
                category=category,
                homeowner=self.request.user,
                budget_min=form.cleaned_data.get('budget_min', 0),
                budget_max=form.cleaned_data.get('budget_max', 0),
                location=form.cleaned_data.get('location', 'South Africa'),
                urgency=form.cleaned_data.get('urgency', 'medium'),
                job_status='pending'
            )
            
            # Handle image uploads
            job_images = form.files.getlist('job_images')
            if job_images:
                for image in job_images:
                    # Save image to gig
                    gig.image.save(image.name, image)
            
            # Redirect to gig detail instead of payment for new jobs
            messages.success(self.request, 'Job created successfully! Professionals will contact you soon.')
            return redirect('gigs:detail', pk=gig.pk)
            
        else:
            # This is a gig-based order
            gig = form.instance.gig
            if gig:
                form.instance.service_provider = gig.hired_provider
                if not form.instance.total_amount:
                    form.instance.total_amount = gig.budget_max
                form.instance.due_date = timezone.now() + timezone.timedelta(days=7)
            
            # Create Stripe payment intent
            try:
                # Check if Stripe is properly configured
                if not hasattr(settings, 'STRIPE_SECRET_KEY') or settings.STRIPE_SECRET_KEY in ['sk_test_your-stripe-secret-key', '']:
                    messages.error(self.request, 'Stripe is not properly configured. Please contact support.')
                    return self.form_invalid(form)
                
                stripe.api_key = settings.STRIPE_SECRET_KEY
                intent = stripe.PaymentIntent.create(
                    amount=int(form.instance.total_amount * 100),  # Convert to cents
                    currency='zar',  # Use South African Rand
                    metadata={
                        'order_id': str(form.instance.pk),
                        'gig_id': str(gig.pk) if gig else '',
                    }
                )
                form.instance.stripe_payment_intent_id = intent.id
            except stripe.error.StripeError as e:
                messages.error(self.request, f'Payment processing error: {str(e)}')
                return self.form_invalid(form)
            except Exception as e:
                messages.error(self.request, f'Payment setup failed: {str(e)}')
                return self.form_invalid(form)
            
            messages.success(self.request, 'Order created! Please complete payment.')
            return super().form_valid(form)


@login_required
def payment_view(request, pk):
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    # Since we're not using Stripe, redirect to payment options page
    messages.info(request, 'Please select your preferred payment method.')
    return redirect('orders:process_payment', pk=order.pk)


@login_required
def payment_confirmation(request, pk):
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if request.method == 'POST':
        payment_intent_id = request.POST.get('payment_intent_id')
        
        try:
            # Check if Stripe is properly configured
            if not hasattr(settings, 'STRIPE_SECRET_KEY') or settings.STRIPE_SECRET_KEY in ['sk_test_your-stripe-secret-key', '']:
                messages.error(request, 'Stripe is not properly configured. Please contact support.')
                return redirect('orders:detail', pk=order.pk)
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                order.mark_as_paid()
                order.accept_order()  # Auto-accept for now
                
                # Send WhatsApp notification for payment confirmation
                try:
                    from whatsapp_service import get_whatsapp_service
                    whatsapp_service = get_whatsapp_service()
                    
                    # Send to homeowner
                    if order.homeowner.phone:
                        payment_details = {
                            'payment_id': payment_intent.id,
                            'amount': str(order.total_amount),
                            'order_id': str(order.pk),
                            'status': 'Completed'
                        }
                        
                        whatsapp_service.send_payment_confirmation(
                            to=order.homeowner.phone,
                            payment_details=payment_details
                        )
                    
                    # Send to service provider
                    if order.service_provider.phone:
                        order_details = {
                            'id': str(order.pk),
                            'service_title': order.gig.title if order.gig else 'Service Order',
                            'amount': str(order.total_amount),
                            'status': 'Paid'
                        }
                        
                        whatsapp_service.send_order_notification(
                            to=order.service_provider.phone,
                            order_details=order_details
                        )
                        
                except Exception as e:
                    # Log error but don't fail payment process
                    logger.error(f"Failed to send WhatsApp payment notification: {e}")
                
                messages.success(request, 'Payment successful! Your order has been placed.')
                return redirect('orders:detail', pk=order.pk)
            else:
                messages.error(request, 'Payment was not successful. Please try again.')
        except stripe.error.StripeError as e:
            messages.error(request, f'Payment error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Payment processing failed: {str(e)}')
    
    return redirect('orders:payment', pk=order.pk)


@login_required
def process_payment_view(request, pk):
    """Process payment with payment method selection and invoice display"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    # Check if order is completed and has a review
    if order.status != 'completed':
        messages.error(request, 'Payment can only be processed for completed orders.')
        return redirect('orders:detail', pk=order.pk)
    
    # Check if review exists
    from reviews.models import Review
    if not Review.objects.filter(order=order, client=request.user).exists():
        messages.error(request, 'Please complete the review first before processing payment.')
        return redirect('reviews:create', order_id=order.pk)
    
    # Check if already paid
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        valid_methods = ['yoco', 'ozow', 'eft', 'in_person']
        if payment_method not in valid_methods:
            messages.error(request, 'Please select a valid payment method.')
        else:
            # Update order with payment method
            order.payment_method = payment_method
            order.save()
            
            if payment_method == 'yoco':
                # Redirect to Yoco payment instructions
                return redirect('orders:yoco_payment', pk=order.pk)
                
            elif payment_method == 'ozow':
                # Redirect to Ozow payment
                return redirect('orders:ozow_payment', pk=order.pk)
                
            elif payment_method == 'eft':
                # Show EFT payment details
                return redirect('orders:eft_payment', pk=order.pk)
                
            elif payment_method == 'in_person':
                # Mark as paid and redirect to thank you page
                order.mark_as_paid()
                messages.success(request, 'Payment confirmed! Thank you for completing the payment.')
                return redirect('orders:payment_thank_you', pk=order.pk)
    
    # Generate invoice data
    from gigs.views_invoice import get_invoice_data
    invoice_data = get_invoice_data(order.gig, order.service_provider, order)
    
    context = {
        'order': order,
        'invoice_data': invoice_data,
        'payment_method_choices': Order.PAYMENT_METHOD_CHOICES,
    }
    
    return render(request, 'orders/process_payment.html', context)


@login_required
def payment_thank_you_view(request, pk):
    """Thank you page after payment completion"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    # Check if payment is completed
    if order.payment_status != 'paid':
        messages.error(request, 'Payment not completed for this order.')
        return redirect('orders:detail', pk=order.pk)
    
    # Check if review exists
    from reviews.models import Review
    review_exists = Review.objects.filter(order=order, client=request.user).exists()
    
    context = {
        'order': order,
        'review_written': review_exists,
    }
    
    return render(request, 'orders/payment_thank_you.html', context)


@login_required
def add_order_message(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.user not in [order.homeowner, order.service_provider]:
        messages.error(request, 'You are not authorized to message on this order.')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        form = OrderMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.order = order
            message.sender = request.user
            message.save()
            
            # Determine the receiver
            if request.user == order.homeowner:
                receiver = order.service_provider
            else:
                receiver = order.homeowner
            
            # Create notification for the receiver
            from notifications.models import Notification
            Notification.objects.create(
                recipient=receiver,
                sender=request.user,
                notification_type='message_received',
                title=f'New message on Order #{order.order_number}',
                message=f'{request.user.get_full_name() or request.user.email} sent you a message: {message.message[:100]}{"..." if len(message.message) > 100 else ""}',
                order=order,
                channels='in_app'
            )
            
            messages.success(request, 'Message sent successfully!')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def accept_order(request, pk):
    order = get_object_or_404(Order, pk=pk, service_provider=request.user)
    
    if order.status == 'pending':
        order.accept_order()
        messages.success(request, 'Order accepted successfully!')
    else:
        messages.warning(request, 'This order cannot be accepted.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def reject_order(request, pk):
    order = get_object_or_404(Order, pk=pk, service_provider=request.user)
    
    if order.status == 'pending':
        order.reject_order()
        messages.info(request, 'Order rejected. The client will be notified.')
    else:
        messages.warning(request, 'This order cannot be rejected.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def start_order_progress(request, pk):
    order = get_object_or_404(Order, pk=pk, service_provider=request.user)
    
    if order.status == 'accepted':
        order.start_progress()
        messages.success(request, 'Order progress started!')
    else:
        messages.warning(request, 'This order cannot be started.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def deliver_order(request, pk):
    order = get_object_or_404(Order, pk=pk, service_provider=request.user)
    
    if order.status == 'in_progress':
        if request.method == 'POST':
            files = request.FILES.getlist('files')
            if files:
                for file in files:
                    order_file = OrderFile.objects.create(
                        file=file,
                        filename=file.name,
                        uploaded_by=request.user
                    )
                    order.delivery_files.add(order_file)
                
                order.deliver_order()
                messages.success(request, 'Order delivered successfully!')
            else:
                messages.error(request, 'Please upload at least one file.')
    else:
        messages.warning(request, 'This order cannot be delivered.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def request_revision(request, pk):
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.status == 'delivered':
        if request.method == 'POST':
            form = OrderRevisionForm(request.POST)
            if form.is_valid():
                revision = form.save(commit=False)
                revision.order = order
                revision.requested_by = request.user
                revision.save()
                
                order.request_revision()
                messages.success(request, 'Revision request submitted!')
                return redirect('orders:detail', pk=order.pk)
    else:
        messages.warning(request, 'This order cannot have revisions requested.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def complete_order(request, pk):
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.status == 'delivered':
        order.complete_order()
        messages.success(request, 'Order completed successfully!')
        
        # Redirect to review creation
        return redirect('reviews:create', order_id=order.pk)
    else:
        messages.warning(request, 'This order cannot be completed.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    # Check if user can cancel (client if pending, either party if not started)
    can_cancel = (
        (request.user == order.homeowner and order.status == 'pending') or
        (order.status in ['pending', 'accepted'] and request.user in [order.homeowner, order.service_provider])
    )
    
    if can_cancel:
        order.cancel_order()
        
        # Refund logic here
        if order.payment_status == 'paid':
            try:
                # Check if Stripe is properly configured
                if not hasattr(settings, 'STRIPE_SECRET_KEY') or settings.STRIPE_SECRET_KEY in ['sk_test_your-stripe-secret-key', '']:
                    messages.warning(request, 'Order cancelled but Stripe is not configured for automatic refunds. Please contact support for manual refund.')
                else:
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    if order.stripe_charge_id:
                        stripe.Refund.create(charge=order.stripe_charge_id)
                        messages.success(request, 'Order cancelled and refund initiated.')
                    else:
                        messages.warning(request, 'Order cancelled but no charge found for refund.')
            except stripe.error.StripeError as e:
                messages.warning(request, f'Order cancelled but refund failed: {str(e)}')
            except Exception as e:
                messages.warning(request, f'Order cancelled but refund processing failed: {str(e)}')
        else:
            messages.success(request, 'Order cancelled successfully.')
    else:
        messages.warning(request, 'This order cannot be cancelled.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def payfast_payment_view(request, pk):
    """Process PayFast payment for South African users"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    # PayFast configuration (you'll need to get these from PayFast)
    payfast_merchant_id = getattr(settings, 'PAYFAST_MERCHANT_ID', '10000100')
    payfast_merchant_key = getattr(settings, 'PAYFAST_MERCHANT_KEY', 'testkey')
    
    # Generate PayFast payment data
    import hashlib
    
    data = {
        'merchant_id': payfast_merchant_id,
        'merchant_key': payfast_merchant_key,
        'return_url': request.build_absolute_uri(f'/orders/{pk}/payment/confirm/'),
        'cancel_url': request.build_absolute_uri(f'/orders/{pk}/process-payment/'),
        'notify_url': request.build_absolute_uri(f'/orders/{pk}/payfast-notify/'),
        'name_first': request.user.first_name or 'Client',
        'name_last': request.user.last_name or 'User',
        'email_address': request.user.email,
        'm_payment_id': str(order.pk),
        'amount': str(order.total_amount),
        'item_name': f'Payment for {order.gig.title}',
        'item_description': f'Order #{order.order_number}',
        'custom_int1': str(order.pk),
        'custom_str1': order.order_number,
    }
    
    # Generate signature
    payload = '&'.join([f'{key}={value}' for key, value in sorted(data.items())])
    signature = hashlib.md5(payload.encode()).hexdigest()
    data['signature'] = signature
    
    context = {
        'order': order,
        'payfast_data': data,
        'payfast_url': 'https://www.payfast.co.za/eng/process'
    }
    
    return render(request, 'orders/payfast_payment.html', context)


@login_required
def yoco_payment_view(request, pk):
    """Show Yoco payment instructions"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    context = {
        'order': order,
        'yoco_phone': getattr(settings, 'YOCO_PHONE', '+27 21 447 5200'),
        'yoco_email': getattr(settings, 'YOCO_EMAIL', 'support@yoco.com')
    }
    
    return render(request, 'orders/yoco_payment.html', context)


@login_required
def eft_payment_view(request, pk):
    """Show EFT payment details"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    # Get active bank account from database
    bank_details = BankAccount.objects.filter(is_active=True).first()
    
    context = {
        'order': order,
        'bank_details': bank_details
    }
    
    return render(request, 'orders/eft_payment.html', context)


@login_required
def confirm_eft_payment(request, pk):
    """Handle EFT payment confirmation from user"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        # Create EFT payment confirmation record
        confirmation, created = EFTPaymentConfirmation.objects.get_or_create(
            order=order,
            user=request.user,
            defaults={
                'notes': f'EFT payment confirmed by {request.user.email}'
            }
        )
        
        messages.success(request, 'Thank you! Your EFT payment confirmation has been received. We will verify the payment within 1-2 business days.')
        return redirect('orders:detail', pk=order.pk)
    
    return redirect('orders:eft_payment', pk=order.pk)


def get_ozow_access_token():
    """Get or refresh Ozow access token"""
    try:
        # Ozow token endpoint
        token_url = 'https://stagingapi.ozow.com/token'
        
        # Prepare token request data
        token_data = {
            'grant_type': 'client_credentials',
            'SiteCode': getattr(settings, 'OZOW_SITE_ID', 'SPH-PRO-001'),
        }
        
        # URL encode the data
        encoded_data = urllib.parse.urlencode(token_data)
        
        headers = {
            'Accept': 'application/json, application/xml',
            'ApiKey': getattr(settings, 'OZOW_API_KEY', 'c7286afbbee74924bdd6bb4c03f3b0f4'),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(token_url, data=encoded_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            token_response = response.json()
            return token_response.get('access_token')
        else:
            logger.error(f"Token request failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Ozow token: {str(e)}")
        return None


@csrf_exempt
@login_required
def ozow_payment_view(request, pk):
    """Process Ozow instant EFT payment"""
    order = get_object_or_404(Order, pk=pk, homeowner=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This order has already been paid for.')
        return redirect('orders:detail', pk=order.pk)
    
    # Generate Ozow payment data - use OrderedDict to preserve parameter order
    from collections import OrderedDict
    data = OrderedDict([
        ('SiteCode', getattr(settings, 'OZOW_SITE_ID', 'SPH-PRO-001')),
        ('CountryCode', 'ZA'),
        ('CurrencyCode', 'ZAR'),
        ('Amount', f"{float(order.total_amount):.2f}"),
        ('TransactionReference', order.order_number),
        ('BankReference', order.order_number),
        ('Customer', request.user.email),
        ('CancelUrl', request.build_absolute_uri(f'/orders/{pk}/process-payment/')),
        ('ErrorUrl', request.build_absolute_uri(f'/orders/{pk}/process-payment/')),
        ('SuccessUrl', request.build_absolute_uri(f'/orders/{pk}/payment/confirm/')),
        ('NotifyUrl', request.build_absolute_uri(f'/orders/{pk}/ozow-notify/')),
        ('IsTest', 'false'),  # CRITICAL: Must be string 'false' for production mode
    ])
    
    # Generate Ozow signature (HashCheck) - using SHA512 as per documentation
    # Concatenate post variable VALUES only (excluding HashCheck) in order they appear
    values_only = ''.join([str(value) for key, value in data.items() if key not in ['HashCheck']])
    # Append secret key and convert to lowercase
    secret_key = getattr(settings, 'OZOW_API_SECRET', 'production-secret')
    hash_string = (values_only + secret_key).lower()
    # Generate SHA512 hash
    signature = hashlib.sha512(hash_string.encode()).hexdigest()
    data['HashCheck'] = signature
    
    # Debug logging
    print(f"=== OZOW HASH DEBUG ===")
    print(f"Values only: {values_only}")
    print(f"Hash string: {hash_string}")
    print(f"Generated HashCheck: {signature}")
    
    try:
        # Make API call to Ozow to get transaction URL
        api_url = 'https://api.ozow.com/postpaymentrequest'
        headers = {
            'Accept': 'application/json, application/xml',
            'ApiKey': getattr(settings, 'OZOW_API_KEY', 'c7286afbbee74924bdd6bb4c03f3b0f4'),
            'Content-Type': 'application/json'
        }
        
        print(f"=== OZOW API DEBUG ===")
        print(f"API URL: {api_url}")
        print(f"Request Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(api_url, json=data, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            api_response = response.json()
            
            if 'url' in api_response and api_response['url']:
                # Store Ozow's transaction ID for verification
                order.ozow_transaction_id = api_response.get('paymentRequestId')
                order.save()
                
                # Redirect to dynamic Ozow payment URL
                return redirect(api_response.get('url'))
            else:
                # Handle error response
                error_msg = api_response.get('errorMessage', 'Unknown error occurred')
                messages.error(request, f'Ozow payment error: {error_msg}')
                return redirect('orders:process_payment', pk=order.pk)
        else:
            # Handle HTTP errors
            messages.error(request, f'Ozow API error: {response.status_code} - {response.text}')
            return redirect('orders:process_payment', pk=order.pk)
            
    except Exception as e:
        logger.error(f"Ozow payment error: {str(e)}")
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('orders:process_payment', pk=order.pk)
        
    except Exception as e:
        logger.error(f"Ozow payment error: {str(e)}")
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('orders:process_payment', pk=order.pk)
