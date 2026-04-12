from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse
from gigs.models import Gig
from .forms import PrivateJobForm
from .models import JobOffer

User = get_user_model()

@login_required
def create_private_job(request, provider_id):
    """Create a private job that only the hired provider can see"""
    
    # Get the service provider
    service_provider = get_object_or_404(User, pk=provider_id, user_type='service_provider')
    
    # Check if user is a homeowner
    if request.user.user_type != 'homeowner':
        messages.error(request, 'Only homeowners can create private jobs.')
        return redirect('gigs:service_providers')
    
    if request.method == 'POST':
        form = PrivateJobForm(request.POST, provider=service_provider)
        if form.is_valid():
            # Create a job offer for this provider
            job_offer = JobOffer.objects.create(
                homeowner=request.user,
                service_provider=service_provider,
                job_title=form.cleaned_data['job_title'],
                job_description=form.cleaned_data['requirements'],
                budget_min=form.cleaned_data.get('budget_min', 50),
                budget_max=form.cleaned_data.get('budget_max', 500),
                status='pending'
            )
            
            messages.success(request, f'Job offer "{form.cleaned_data["job_title"]}" sent to {service_provider.get_full_name() or service_provider.email}. They will review and submit an estimate.')
            return redirect('orders:job_offers_sent')
        else:
            # Form has errors, re-render with form and errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
            
            # Ensure form has POST data for template rendering
            context = {
                'provider': service_provider,
                'form': form,
            }
            return render(request, 'orders/create_private_job.html', context)
    else:
        form = PrivateJobForm(provider=service_provider, initial={
            'job_title': '',
            'budget_min': 50,
            'budget_max': 500,
            'requirements': '',
            'start_date': '',
            'completion_date': '',
            'category': '',
        })
    
    context = {
        'provider': service_provider,
        'form': form,
    }
    
    return render(request, 'orders/create_private_job.html', context)
