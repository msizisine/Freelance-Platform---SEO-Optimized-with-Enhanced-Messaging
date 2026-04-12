from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Avg, Count
from django.http import JsonResponse
from .models import Review, ReviewResponse, ReviewHelpful, FreelancerStats
from .forms import ReviewForm, ReviewResponseForm
from orders.models import Order


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/review_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        order_id = self.kwargs.get('order_id')
        if order_id:
            order = get_object_or_404(Order, pk=order_id, homeowner=self.request.user)
            initial['order'] = order
            initial['client'] = self.request.user
            initial['service_provider'] = order.service_provider
            initial['gig'] = order.gig
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        if order_id:
            order = get_object_or_404(Order, pk=order_id, homeowner=self.request.user)
            context['order'] = order
        return context
    
    def form_valid(self, form):
        # Get the order from URL kwargs
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, pk=order_id, homeowner=self.request.user)
        
        # Check if user can review this order
        if order.status != 'completed':
            messages.error(self.request, 'You can only review completed orders.')
            return self.form_invalid(form)
        
        # Check if review already exists
        if Review.objects.filter(order=order, client=self.request.user).exists():
            messages.error(self.request, 'You have already reviewed this order.')
            return self.form_invalid(form)
        
        # Set the order and other required fields
        form.instance.order = order
        form.instance.client = self.request.user
        form.instance.service_provider = order.service_provider
        form.instance.gig = order.gig
        
        messages.success(self.request, 'Your review has been submitted successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to order detail page after review submission
        return reverse_lazy('orders:detail', kwargs={'pk': self.object.order.pk})


class ReviewDetailView(DetailView):
    model = Review
    template_name = 'reviews/review_detail.html'
    context_object_name = 'review'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        review = self.get_object()
        
        context['helpful_count'] = review.helpful_votes.filter(is_helpful=True).count()
        context['not_helpful_count'] = review.helpful_votes.filter(is_helpful=False).count()
        
        if self.request.user.is_authenticated:
            context['user_voted'] = review.helpful_votes.filter(
                user=self.request.user
            ).exists()
        
        return context


@login_required
def review_response_create(request, review_pk):
    review = get_object_or_404(Review, pk=review_pk)
    
    # Only service provider can respond to reviews about them
    if review.service_provider != request.user:
        messages.error(request, 'You can only respond to reviews about your work.')
        return redirect('reviews:detail', pk=review.pk)
    
    # Check if response already exists
    if ReviewResponse.objects.filter(review=review).exists():
        messages.error(request, 'You have already responded to this review.')
        return redirect('reviews:detail', pk=review.pk)
    
    if request.method == 'POST':
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.review = review
            response.service_provider = request.user
            response.save()
            
            messages.success(request, 'Your response has been posted!')
            return redirect('reviews:detail', pk=review.pk)
    else:
        form = ReviewResponseForm()
    
    context = {
        'review': review,
        'form': form,
    }
    
    return render(request, 'reviews/review_response.html', context)


@login_required
def toggle_helpful_vote(request, review_pk):
    review = get_object_or_404(Review, pk=review_pk)
    user = request.user
    
    # Check if user already voted
    existing_vote = ReviewHelpful.objects.filter(review=review, user=user).first()
    
    if existing_vote:
        # Toggle the vote
        existing_vote.is_helpful = not existing_vote.is_helpful
        existing_vote.save()
        action = 'updated'
    else:
        # Create new vote
        ReviewHelpful.objects.create(review=review, user=user, is_helpful=True)
        action = 'created'
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'action': action,
            'helpful_count': review.helpful_votes.filter(is_helpful=True).count(),
            'not_helpful_count': review.helpful_votes.filter(is_helpful=False).count(),
        })
    
    return redirect('reviews:detail', pk=review.pk)


@login_required
def freelancer_reviews(request, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    freelancer = get_object_or_404(User, pk=user_id, user_type='service_provider')
    reviews = freelancer.reviews_received.filter(is_public=True).order_by('-created_at')
    
    # Calculate stats
    stats = {
        'total_reviews': reviews.count(),
        'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
    }
    
    # Rating breakdown
    for i in range(1, 6):
        stats[f'{i}_star_count'] = reviews.filter(rating=i).count()
        stats[f'{i}_star_percent'] = 0
    
    if stats['total_reviews'] > 0:
        for i in range(1, 6):
            stats[f'{i}_star_percent'] = (stats[f'{i}_star_count'] / stats['total_reviews']) * 100
    
    context = {
        'freelancer': freelancer,
        'reviews': reviews,
        'stats': stats,
    }
    
    return render(request, 'reviews/freelancer_reviews.html', context)


@login_required
def homeowner_reviews(request, user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    homeowner = get_object_or_404(User, pk=user_id, user_type='homeowner')
    # Get reviews where homeowner is client (reviews they wrote)
    reviews = Review.objects.filter(client=homeowner, is_public=True).order_by('-created_at')
    
    # Calculate stats
    stats = {
        'total_reviews': reviews.count(),
        'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        'five_star': reviews.filter(rating=5).count(),
        'four_star': reviews.filter(rating=4).count(),
        'three_star': reviews.filter(rating=3).count(),
        'two_star': reviews.filter(rating=2).count(),
        'one_star': reviews.filter(rating=1).count(),
    }
    
    # Calculate rating distribution percentages
    total = stats['total_reviews']
    if total > 0:
        for i in range(1, 6):
            stats[f'{i}_star_percent'] = (stats[f'{i}_star'] / total) * 100
    else:
        for i in range(1, 6):
            stats[f'{i}_star_percent'] = 0
    
    context = {
        'homeowner': homeowner,
        'reviews': reviews,
        'stats': stats,
    }
    
    return render(request, 'reviews/homeowner_reviews.html', context)
