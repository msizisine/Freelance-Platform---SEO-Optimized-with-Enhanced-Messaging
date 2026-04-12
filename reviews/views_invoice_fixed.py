from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from gigs.models import Gig
from reviews.models import Review
from orders.models import Order

@login_required
def create_review_with_invoice(request, user_id, order_id, job_id):
    """Create review with invoice context"""
    # Convert user_id to integer to avoid TypeError
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        messages.error(request, 'Invalid user ID provided.')
        return redirect('gigs:detail', pk=job_id)
    
    service_provider = get_object_or_404(get_user_model(), pk=user_id)
    gig = get_object_or_404(Gig, pk=job_id)
    order = get_object_or_404(Order, pk=order_id)
    
    # Check if user is the homeowner who completed the job
    if request.user != gig.homeowner:
        messages.error(request, 'Only the job owner can create reviews.')
        return redirect('gigs:detail', pk=job_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if rating:
            # Check if review already exists
            if Review.objects.filter(order=order, client=gig.homeowner).exists():
                messages.warning(request, 'You have already submitted a review for this order.')
                return redirect('reviews:detail', pk=Review.objects.get(order=order, client=gig.homeowner).pk)
            
            # Create review
            review = Review.objects.create(
                client=gig.homeowner,
                service_provider=service_provider,
                gig=gig,
                order=order,
                rating=int(rating),
                comment=comment
            )
            
            messages.success(request, 'Thank you! Your review has been submitted.')
            return redirect('reviews:thank_you')
        else:
            messages.error(request, 'Please provide a rating.')
    
    context = {
        'gig': gig,
        'service_provider': service_provider,
        'order': order,
        'rating_choices': range(1, 6),
    }
    return render(request, 'reviews/create_review_with_invoice.html', context)

@login_required
def thank_you(request):
    """Thank you page after review submission"""
    return render(request, 'reviews/thank_you.html')
