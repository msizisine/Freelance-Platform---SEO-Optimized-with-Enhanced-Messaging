from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.db.models import Avg, Count, Sum, Q
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from .forms import ServiceProviderProfileForm, HomeownerProfileForm, PortfolioForm, WorkExperienceForm, ProfessionalReferenceForm
from core.models import Portfolio, WorkExperience, ProfessionalReference, PortfolioImage
from gigs.models import Gig
from reviews.models import Review
from orders.models import Order

@login_required
def dashboard(request):
    """User dashboard view with payment functionality for service providers"""
    user = request.user
    context = {
        'user': user,
        'recent_orders': Order.objects.filter(homeowner=user).order_by('-created_at')[:5],
        'active_orders': Order.objects.filter(homeowner=user, status='in_progress').count(),
        'completed_orders': Order.objects.filter(homeowner=user, status='completed').count(),
        'pending_orders': Order.objects.filter(homeowner=user, status='pending').count(),
    }
    
    # Add payment functionality for service providers
    if user.user_type == 'service_provider':
        try:
            from core.services.payment_service import PaymentProcessingService
            from core.models_payments import ProviderEarnings, ProviderPayout, PaymentTransaction
            
            # Get payment statistics
            available_balance = PaymentProcessingService.get_provider_balance(user)
        except ImportError:
            # Handle case where payment service is not available
            available_balance = 0
            PaymentProcessingService = None
            ProviderEarnings = None
            ProviderPayout = None
            PaymentTransaction = None
        if PaymentProcessingService:
            recent_transactions = PaymentProcessingService.get_provider_transaction_history(user, limit=5)
        else:
            recent_transactions = []
        
        if ProviderPayout:
            pending_payouts = ProviderPayout.objects.filter(
                provider=user, 
                status__in=['requested', 'processing', 'approved']
            ).aggregate(total=Sum('net_amount'))['total'] or 0
        else:
            pending_payouts = 0
        
        # Get available earnings for immediate payment request
        if ProviderEarnings:
            available_earnings = ProviderEarnings.objects.filter(
                provider=user,
                status='available'
            ).order_by('-created_at')
        else:
            available_earnings = []
        
        if ProviderEarnings:
            total_earnings = ProviderEarnings.objects.filter(provider=user).aggregate(
                total=Sum('net_amount')
            )['total'] or 0
        else:
            total_earnings = 0
            
        if ProviderPayout:
            completed_payouts = ProviderPayout.objects.filter(
                provider=user, 
                status='completed'
            ).aggregate(total=Sum('net_amount'))['total'] or 0
        else:
            completed_payouts = 0
        
        context.update({
            'available_balance': available_balance,
            'recent_transactions': recent_transactions,
            'pending_payouts': pending_payouts,
            'available_earnings': available_earnings,
            'total_earnings': total_earnings,
            'completed_payouts': completed_payouts,
        })
    
    return render(request, 'users/dashboard.html', context)

User = get_user_model()


class ProfileView(DetailView):
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Add common context
        context.update({
            'completed_orders': Order.objects.filter(homeowner=user, status='completed').count(),
            'active_orders': Order.objects.filter(homeowner=user, status='in_progress').count(),
            'total_spent': Order.objects.filter(homeowner=user, status='completed').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
        })
        
        if user.user_type == 'service_provider':
            # Service provider specific context
            # Use Gig model for job statistics
            total_jobs = Gig.objects.filter(hired_provider=user).count()
            completed_orders = Gig.objects.filter(hired_provider=user, job_status='completed').count()
            active_orders = Gig.objects.filter(hired_provider=user, job_status__in=['pending', 'accepted']).count()
            
            # Calculate earnings from Order model (financial data)
            total_earnings = Order.objects.filter(service_provider=user, status__in=['completed', 'delivered']).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            # Calculate response rate (jobs responded to within 24 hours)
            from datetime import timedelta
            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
            response_rate = 0
            if total_jobs > 0:
                # Calculate based on job applications or offers responded to
                from gigs.models import JobApplication
                responded_applications = JobApplication.objects.filter(
                    service_provider=user,
                    applied_at__gte=twenty_four_hours_ago,
                    status__in=['accepted', 'rejected']
                ).count()
                response_rate = (responded_applications / total_jobs) * 100
            
            # Calculate completion rate
            completion_rate = 0
            if total_jobs > 0:
                completion_rate = (completed_orders / total_jobs) * 100
            
            # Get total reviews
            total_reviews = Review.objects.filter(service_provider=user).count()
            
            # Calculate rating distribution
            rating_distribution = Review.objects.filter(service_provider=user).values('rating').annotate(
                count=Count('id')
            ).order_by('rating')
            
            context.update({
                'portfolio_items': user.portfolio_items.all(),
                'work_experiences': user.work_experiences.all(),
                'professional_references': user.professional_references.all(),
                'average_rating': Review.objects.filter(service_provider=user).aggregate(Avg('rating'))['rating__avg'] or 0,
                'total_orders': total_jobs,
                'completed_orders': completed_orders,
                'active_orders': active_orders,
                'total_earnings': total_earnings,
                'response_rate': response_rate,
                'completion_rate': completion_rate,
                'total_reviews': total_reviews,
                'rating_distribution': rating_distribution,
                'years_experience': user.years_experience or 0,
            })
        else:
            # Homeowner specific context
            context.update({
                'average_rating': Review.objects.filter(client=user).aggregate(Avg('rating'))['rating__avg'] or 0,
                'total_jobs_posted': Gig.objects.filter(homeowner=user).count(),
                'completed_orders': Order.objects.filter(homeowner=user, status='completed').count(),
            })
        
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:my_profile')
    
    def get_object(self):
        # Return the current logged-in user instead of looking up by pk
        return self.request.user
    
    def get_template_names(self):
        user = self.request.user
        if user.user_type == 'service_provider':
            return ['users/profile_edit_service_provider.html']
        else:
            return ['users/profile_edit.html']
    
    def get_form_class(self):
        user = self.request.user
        if user.user_type == 'service_provider':
            return ServiceProviderProfileForm
        else:
            return HomeownerProfileForm
    
    def get_object(self, queryset=None):
        # Return the current logged-in user for editing
        return self.request.user
    
    def form_valid(self, form):
        try:
            print(f"Form is valid: {form.is_valid()}")
            print(f"Form cleaned data: {form.cleaned_data}")
            print(f"User type: {self.request.user.user_type}")
            
            # Save the form
            response = super().form_valid(form)
            print(f"Save response: {response}")
            
            messages.success(self.request, 'Profile updated successfully!')
            return response
            
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            messages.error(self.request, f'Error updating profile: {str(e)}')
            return self.form_invalid(form)


from core.models import Portfolio, WorkExperience, ProfessionalReference, PortfolioImage


@login_required
def portfolio_edit(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk, service_provider=request.user)
    
    if request.method == 'POST':
        form = PortfolioForm(request.POST, request.FILES, instance=portfolio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Portfolio item updated successfully!')
            return redirect('users:profile')
    else:
        form = PortfolioForm(instance=portfolio)
    
    return render(request, 'users/portfolio_form.html', {'form': form, 'title': 'Edit Portfolio Item'})


@login_required
def portfolio_delete(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk, service_provider=request.user)
    
    if request.method == 'POST':
        portfolio.delete()
        messages.success(request, 'Portfolio item deleted successfully!')
        return redirect('users:profile_edit')
    
    return render(request, 'users/portfolio_delete.html', {'portfolio': portfolio})


@login_required
def portfolio_create(request):
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        form = PortfolioForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.service_provider = request.user
            portfolio.save()
            print("Portfolio saved with ID:", portfolio.id)
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for image in images:
                PortfolioImage.objects.create(
                    portfolio=portfolio,
                    image=image
                )
            print(f"Created {len(images)} images for portfolio {portfolio.id}")
            
            messages.success(request, 'Portfolio item added successfully!')
            return redirect('users:profile_edit')
        else:
            # Add debugging to see form errors
            print("Form is not valid. Errors:", form.errors)
            print("Form cleaned_data:", form.cleaned_data if hasattr(form, 'cleaned_data') else 'No cleaned_data')
            for field, errors in form.errors.items():
                print(f"Field {field}: {errors}")
            messages.error(request, f'Please correct the errors below: {form.errors}')
    else:
        form = PortfolioForm()
    
    return render(request, 'users/portfolio_form.html', {'form': form, 'title': 'Add Portfolio Item'})


@login_required
def reference_create(request):
    if request.method == 'POST':
        form = ProfessionalReferenceForm(request.POST)
        if form.is_valid():
            reference = form.save(commit=False)
            reference.service_provider = request.user
            reference.save()
            messages.success(request, 'Professional reference added successfully!')
            return redirect('users:profile_edit')
    else:
        form = ProfessionalReferenceForm()
    
    return render(request, 'users/reference_form.html', {'form': form, 'title': 'Add Professional Reference'})


@login_required
def reference_delete(request, pk):
    reference = get_object_or_404(ProfessionalReference, pk=pk, service_provider=request.user)
    
    if request.method == 'POST':
        reference.delete()
        messages.success(request, 'Reference deleted successfully!')
        return redirect('users:profile_edit')
    
    return render(request, 'users/reference_delete.html', {'reference': reference})


@login_required
def dashboard(request):
    user = request.user
    
    if user.user_type == 'service_provider':
        # Service Provider Dashboard
        available_jobs = Gig.objects.filter(is_active=True, hired_provider__isnull=True)  # Available jobs for new applications
        
        # Jobs the service provider is working on (accepted/active jobs)
        active_jobs = Gig.objects.filter(
            Q(hired_provider=user) | Q(applications__service_provider=user, applications__status='accepted')
        ).filter(job_status__in=['accepted', 'active']).distinct()
        
        # All jobs the service provider was hired for (including completed)
        hired_jobs = Gig.objects.filter(hired_provider=user)
        
        # Jobs the service provider has applied to
        applied_jobs = Gig.objects.filter(applications__service_provider=user).distinct()
        
        # Calculate earnings from completed orders
        completed_orders = Order.objects.filter(
            service_provider=user,
            status='completed'
        )
        
        # Completed jobs - count based on completed orders for consistency
        completed_jobs = completed_orders
        total_earnings = completed_orders.aggregate(
            total=Coalesce(Sum('total_amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')
        
        # Calculate pending payments (accepted orders not yet paid)
        pending_payments = Order.objects.filter(
            service_provider=user,
            status__in=['accepted', 'in_progress', 'delivered'],
            payment_status='pending'
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')
        
        context = {
            'user_type': 'service_provider',
            'posted_jobs': available_jobs,  # Available jobs they can apply to
            'applied_jobs': applied_jobs,  # Jobs they've applied to
            'active_jobs': active_jobs,  # Jobs they're working on
            'hired_jobs': hired_jobs,  # All jobs they were hired for
            'completed_jobs': completed_jobs,  # Jobs they've completed
            'total_earnings': total_earnings,  # Earnings from completed jobs
            'pending_payments': pending_payments,  # Pending payments
            'profile_completion': 75,  # Would calculate from profile completeness
        }
    else:
        # Homeowner Dashboard
        my_jobs = Gig.objects.filter(homeowner=user)
        # Active jobs include accepted and active jobs (not completed)
        active_jobs = my_jobs.filter(job_status__in=['accepted', 'active'])
        completed_jobs = my_jobs.filter(job_status='completed')
        # Pending jobs include open and pending jobs
        pending_jobs = my_jobs.filter(job_status__in=['open', 'pending'])
        
        context = {
            'user_type': 'homeowner',
            'my_jobs': my_jobs,
            'active_jobs': active_jobs,
            'completed_jobs': completed_jobs,
            'pending_jobs': pending_jobs,
            'total_spent': 0,  # Would calculate from completed jobs
            'jobs_posted': my_jobs.count(),
        }
    
    return render(request, f'users/dashboard_{user.user_type}.html', context)


@login_required
def portfolio_view(request, user_id):
    """View all portfolio items for a specific user"""
    profile_user = get_object_or_404(User, pk=user_id)
    portfolio_items = profile_user.portfolio_items.all()
    
    context = {
        'profile_user': profile_user,
        'portfolio_items': portfolio_items,
        'total_items': portfolio_items.count(),
    }
    return render(request, 'users/portfolio_view.html', context)


@login_required
def user_reviews(request, user_id):
    """View all reviews for a specific user"""
    profile_user = get_object_or_404(User, pk=user_id)
    
    # Get reviews where user is either service provider (receiving reviews) or homeowner (leaving reviews)
    reviews_received = Review.objects.filter(order__service_provider=profile_user).order_by('-created_at')
    reviews_left = Review.objects.filter(client=profile_user).order_by('-created_at')
    
    context = {
        'profile_user': profile_user,
        'reviews_received': reviews_received,
        'reviews_left': reviews_left,
        'total_reviews_received': reviews_received.count(),
        'total_reviews_left': reviews_left.count(),
        'average_rating_received': reviews_received.aggregate(Avg('rating'))['rating__avg'] or 0,
        'average_rating_left': reviews_left.aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    return render(request, 'users/user_reviews.html', context)


@login_required
def my_profile(request):
    """View the current user's profile"""
    return ProfileView.as_view()(request, pk=request.user.pk)


@login_required
def send_message(request, user_id):
    """Send message to a user via platform, SMS, or WhatsApp"""
    from django.http import JsonResponse
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_POST
    from messaging.models import Conversation, Message, MessageNotification
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    recipient = get_object_or_404(User, pk=user_id)
    sender = request.user
    
    # Validate user types
    if sender.user_type != 'homeowner' or recipient.user_type != 'service_provider':
        return JsonResponse({'success': False, 'error': 'Invalid user types for messaging'})
    
    message_method = request.POST.get('message_method', 'platform')
    message_content = request.POST.get('message_content', '').strip()
    
    if not message_content:
        return JsonResponse({'success': False, 'error': 'Message content is required'})
    
    try:
        if message_method == 'platform':
            # Create platform message
            conversation = Conversation.objects.filter(
                participants__in=[sender, recipient]
            ).annotate(
                participant_count=Count('participants')
            ).filter(participant_count=2).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(sender, recipient)
            
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=message_content
            )
            
            # Create notification for recipient
            MessageNotification.objects.create(
                user=recipient,
                message=message
            )
            
            return JsonResponse({
                'success': True,
                'conversation_id': conversation.pk,
                'message': 'Platform message sent successfully'
            })
            
        elif message_method in ['sms', 'whatsapp']:
            # For SMS/WhatsApp, we'll simulate the external messaging
            # In a real implementation, you would integrate with SMS/WhatsApp APIs
            
            # Log the external message attempt
            print(f"External message ({message_method}) to {recipient.email}: {message_content}")
            
            # Also create a platform message record for tracking
            conversation = Conversation.objects.filter(
                participants__in=[sender, recipient]
            ).annotate(
                participant_count=Count('participants')
            ).filter(participant_count=2).first()
            
            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(sender, recipient)
            
            # Create message with external method indicator
            external_content = f"[{message_method.upper()}] {message_content}"
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=external_content
            )
            
            # Create notification
            MessageNotification.objects.create(
                user=recipient,
                message=message
            )
            
            # Simulate SMS/WhatsApp sending (in production, use actual APIs)
            if recipient.phone:
                # Here you would integrate with:
                # - Twilio for SMS
                # - WhatsApp Business API for WhatsApp
                success = simulate_external_message(
                    method=message_method,
                    phone_number=recipient.phone,
                    message=message_content,
                    sender_name=sender.get_full_name() or sender.email
                )
                
                if success:
                    return JsonResponse({
                        'success': True,
                        'conversation_id': conversation.pk,
                        'message': f'{message_method.upper()} message sent successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': f'Failed to send {message_method.upper()} message'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Recipient has not added their phone number'
                })
                
        else:
            return JsonResponse({'success': False, 'error': 'Invalid message method'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def simulate_external_message(method, phone_number, message, sender_name):
    """
    Simulate sending external SMS/WhatsApp messages.
    In production, replace this with actual API calls to Twilio (SMS) or WhatsApp Business API.
    """
    try:
        # Simulate API call delay
        import time
        time.sleep(0.5)
        
        # Log the message (in production, this would be actual API calls)
        print(f"=== EXTERNAL MESSAGE ===")
        print(f"Method: {method.upper()}")
        print(f"To: {phone_number}")
        print(f"From: {sender_name}")
        print(f"Message: {message}")
        print(f"Status: Sent")
        print("======================")
        
        # Simulate success (in production, check actual API response)
        return True
        
    except Exception as e:
        print(f"Error sending {method}: {e}")
        return False
