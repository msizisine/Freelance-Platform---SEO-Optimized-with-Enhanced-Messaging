from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import JobOffer
from .forms import JobEstimateForm

User = get_user_model()


@login_required
def submit_estimate(request, offer_id):
    """Service provider submits an estimate for a job offer"""
    
    job_offer = get_object_or_404(JobOffer, pk=offer_id)
    
    # Check if user is the service provider for this offer
    if request.user != job_offer.service_provider:
        messages.error(request, 'You can only submit estimates for your own job offers.')
        return redirect('orders:job_offers_received')
    
    # Check if estimate has already been submitted
    if job_offer.status != 'pending':
        messages.error(request, 'This job offer has already been processed.')
        return redirect('orders:job_offers_received')
    
    if request.method == 'POST':
        form = JobEstimateForm(request.POST, instance=job_offer, service_provider=request.user)
        if form.is_valid():
            job_offer = form.save(commit=False)
            job_offer.status = 'submitted'
            job_offer.submitted_at = timezone.now()
            job_offer.save()
            
            messages.success(request, f'Estimate submitted for "{job_offer.job_title}". The homeowner will review your proposal.')
            return redirect('orders:job_offers_received')
    else:
        form = JobEstimateForm(instance=job_offer, service_provider=request.user)
    
    context = {
        'job_offer': job_offer,
        'form': form,
    }
    
    return render(request, 'orders/submit_estimate.html', context)


@login_required
def review_estimates(request):
    """Homeowner reviews submitted estimates"""
    
    if request.user.user_type != 'homeowner':
        messages.error(request, 'Only homeowners can review estimates.')
        return redirect('users:dashboard')
    
    # Get all job offers for this homeowner with submitted estimates
    job_offers = JobOffer.objects.filter(
        homeowner=request.user,
        status='submitted'
    ).order_by('-submitted_at')
    
    context = {
        'job_offers': job_offers,
    }
    
    return render(request, 'orders/review_estimates.html', context)


@login_required
def approve_estimate(request, offer_id):
    """Homeowner approves an estimate and creates a job"""
    
    job_offer = get_object_or_404(JobOffer, pk=offer_id)
    
    # Check if user is the homeowner for this offer
    if request.user != job_offer.homeowner:
        messages.error(request, 'You can only approve estimates for your own job offers.')
        return redirect('orders:review_estimates')
    
    # Check if estimate is submitted
    if job_offer.status != 'submitted':
        messages.error(request, 'This estimate cannot be approved.')
        return redirect('orders:review_estimates')
    
    if request.method == 'POST':
        # Approve the estimate and create a job
        order = job_offer.approve()
        
        messages.success(request, f'Estimate approved! Job "{job_offer.job_title}" has been created and assigned to {job_offer.service_provider.get_full_name() or job_offer.service_provider.email}.')
        return redirect('orders:detail', pk=str(order.pk))
    
    context = {
        'job_offer': job_offer,
    }
    
    return render(request, 'orders/approve_estimate.html', context)


@login_required
def decline_estimate(request, offer_id):
    """Homeowner declines an estimate"""
    
    job_offer = get_object_or_404(JobOffer, pk=offer_id)
    
    # Check if user is the homeowner for this offer
    if request.user != job_offer.homeowner:
        messages.error(request, 'You can only decline estimates for your own job offers.')
        return redirect('orders:review_estimates')
    
    # Check if estimate is submitted
    if job_offer.status != 'submitted':
        messages.error(request, 'This estimate cannot be declined.')
        return redirect('orders:review_estimates')
    
    if request.method == 'POST':
        job_offer.status = 'declined'
        job_offer.declined_at = timezone.now()
        job_offer.save()
        
        messages.success(request, f'Estimate for "{job_offer.job_title}" has been declined.')
        return redirect('orders:review_estimates')
    
    context = {
        'job_offer': job_offer,
    }
    
    return render(request, 'orders/decline_estimate.html', context)


@login_required
def job_offers_received(request):
    """Service provider views job offers received"""
    
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Only service providers can view job offers.')
        return redirect('users:dashboard')
    
    # Get all job offers for this service provider
    job_offers = JobOffer.objects.filter(
        service_provider=request.user
    ).order_by('-created_at')
    
    context = {
        'job_offers': job_offers,
    }
    
    return render(request, 'orders/job_offers_received.html', context)


@login_required
def job_offers_sent(request):
    """Homeowner views job offers sent"""
    
    if request.user.user_type != 'homeowner':
        messages.error(request, 'Only homeowners can view sent job offers.')
        return redirect('users:dashboard')
    
    # Get all job offers sent by this homeowner
    job_offers = JobOffer.objects.filter(
        homeowner=request.user
    ).order_by('-created_at')
    
    context = {
        'job_offers': job_offers,
    }
    
    return render(request, 'orders/job_offers_sent.html', context)
