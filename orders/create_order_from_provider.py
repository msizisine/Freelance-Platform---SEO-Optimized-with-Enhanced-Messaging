from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse
from gigs.models import Gig
from .forms import OrderForm, JobCreationForm

User = get_user_model()

@login_required
def create_order_from_provider(request, provider_id=None):
    """Create an order for a job (can be from provider or generic)"""
    
    # If provider_id is provided, get the service provider
    service_provider = None
    if provider_id:
        service_provider = get_object_or_404(User, pk=provider_id, user_type='service_provider')
    
    # Check if user is a homeowner
    if request.user.user_type != 'homeowner':
        messages.error(request, 'Only homeowners can create orders.')
        return redirect('gigs:list')
    
    if request.method == 'POST':
        # Use JobCreationForm for new jobs, OrderForm for provider-specific jobs
        if provider_id:
            form = OrderForm(request.POST)
        else:
            form = JobCreationForm(request.POST, request.FILES)
            
        if form.is_valid():
            if provider_id:
                # This is an order from existing gig
                order = form.save(commit=False)
                
                # Get gig from form
                gig = form.cleaned_data['gig']
                
                order.gig = gig
                order.homeowner = request.user
                order.service_provider = service_provider
                order.save()
                
                success_message = f'Order created for "{gig.title}"'
                success_message += f' with {service_provider.get_full_name() or service_provider.email}'
                
                messages.success(request, success_message)
                return redirect('orders:detail', pk=order.pk)
            else:
                # This is a new job creation - create gig only
                from gigs.models import Category
                
                # Get category from form
                category = form.cleaned_data.get('category')
                
                # Create a new gig from form data
                gig = Gig.objects.create(
                    title=form.cleaned_data.get('job_title', 'New Job'),
                    description=form.cleaned_data.get('description', ''),
                    category=category,
                    homeowner=request.user,
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
                
                messages.success(request, 'Job created successfully! Professionals will contact you soon.')
                return redirect('gigs:detail', pk=gig.pk)
    else:
        # Set initial data based on whether this is a new job or order from provider
        if provider_id:
            initial_data = {
                'total_amount': 500,
                'requirements': '',
                'due_date': '',
            }
        else:
            initial_data = {}
        
        if service_provider:
            initial_data['requirements'] = f"Service request for {service_provider.get_full_name() or service_provider.email}"
        
        if provider_id:
            form = OrderForm(initial=initial_data)
        else:
            form = JobCreationForm(initial=initial_data)
    
    context = {
        'provider': service_provider,
        'form': form,
        'is_generic': not bool(service_provider),
    }
    
    return render(request, 'orders/create_from_provider.html', context)
