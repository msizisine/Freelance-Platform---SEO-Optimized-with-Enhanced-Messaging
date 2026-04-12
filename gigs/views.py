from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import reverse
from django.db.models import Avg, Count, Sum, Q
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from .utils import generate_invoice_pdf
from .models import Gig, Category, Subcategory, JobApplication, QuotationRequest, QuotationResponse, QuotationRequestProvider, GigPackage, GigRequirement, GigFAQ, GigGallery
from .forms import GigForm, JobApplicationForm, QuotationRequestForm, QuotationResponseForm, QuotationRequestWithProvidersForm, UpdateQuotationRequestForm

User = get_user_model()

def close_expired_quotations():
    """Close all quotation requests that have passed their deadline"""
    from django.utils import timezone
    
    # Get all quotations that are still receiving responses but deadline has passed
    expired_quotations = QuotationRequest.objects.filter(
        status='receiving_responses',
        response_deadline__lt=timezone.now()
    )
    
    closed_count = 0
    for quotation in expired_quotations:
        quotation.status = 'evaluation_period'
        quotation.save()
        closed_count += 1
    
    return closed_count

# Class-based views
class GigListView(ListView):
    model = Gig
    template_name = 'gigs/gig_list.html'
    context_object_name = 'gigs'
    paginate_by = 12

    def get_queryset(self):
        queryset = Gig.objects.filter(is_active=True, hired_provider__isnull=True).select_related('homeowner', 'category')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        # Category filter
        category_name = self.request.GET.get('category')
        if category_name:
            queryset = queryset.filter(category__name=category_name)
        
        # Urgency filter
        urgency = self.request.GET.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        
        # Location filter
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(budget_min__gte=min_price)
        if max_price:
            queryset = queryset.filter(budget_max__lte=max_price)
        
        # Sort options
        sort_by = self.request.GET.get('sort', 'created_desc')
        if sort_by == 'created_asc':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'title_asc':
            queryset = queryset.order_by('title')
        elif sort_by == 'title_desc':
            queryset = queryset.order_by('-title')
        elif sort_by == 'budget_low':
            queryset = queryset.order_by('budget_min')
        elif sort_by == 'budget_high':
            queryset = queryset.order_by('-budget_max')
        else:  # created_desc
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['urgency_filter'] = self.request.GET.get('urgency', '')
        context['location_filter'] = self.request.GET.get('location', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        context['sort_by'] = self.request.GET.get('sort', 'created_desc')
        
        # Calculate statistics
        queryset = self.get_queryset()
        context['total_gigs'] = queryset.count()
        context['avg_budget'] = queryset.aggregate(
            avg=Avg('budget_min'))['avg'] or 0
        
        return context

class GigDetailView(DetailView):
    model = Gig
    template_name = 'gigs/gig_detail.html'
    context_object_name = 'gig'

    def dispatch(self, request, *args, **kwargs):
        gig = self.get_object()
        
        # If job has been hired, restrict access to hired provider and homeowner only
        if gig.hired_provider:
            if not request.user.is_authenticated:
                messages.error(request, 'This job has been assigned and is only visible to the assigned provider and job owner.')
                return redirect('core:home')
            
            if request.user != gig.homeowner and request.user != gig.hired_provider:
                messages.error(request, 'This job has been assigned and is only visible to the assigned provider and job owner.')
                return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gig = self.get_object()
        
        # Get related gigs
        context['related_gigs'] = Gig.objects.filter(
            category=gig.category,
            is_active=True,
            hired_provider__isnull=True
        ).exclude(pk=gig.pk)[:4]
        
        # Check if user has applied
        if self.request.user.is_authenticated:
            context['has_applied'] = JobApplication.objects.filter(
                gig=gig,
                service_provider=self.request.user
            ).exists()
            
            # Check if user is the homeowner
            context['is_job_homeowner'] = self.request.user == gig.homeowner
            
            # Check if user can accept/reject (for private jobs)
            context['can_accept_reject'] = (
                gig.is_private and 
                self.request.user.user_type == 'service_provider' and
                gig.hired_provider == self.request.user
            )
            
            # Get applications for homeowners
            if self.request.user == gig.homeowner:
                context['applications'] = JobApplication.objects.filter(
                    gig=gig
                ).select_related('service_provider', 'service_provider__profile').order_by('-applied_at')
            
            # Check if homeowner can leave a review
            if self.request.user == gig.homeowner and gig.job_status == 'completed':
                from reviews.models import Review
                existing_review = Review.objects.filter(
                    order__gig=gig,
                    client=self.request.user
                ).first()
                context['can_leave_review'] = not bool(existing_review)
                context['existing_review'] = existing_review
            else:
                context['can_leave_review'] = False
                context['existing_review'] = None
        
        return context

class GigCreateView(LoginRequiredMixin, CreateView):
    model = Gig
    form_class = GigForm
    template_name = 'gigs/gig_form.html'

    def form_valid(self, form):
        form.instance.homeowner = self.request.user
        messages.success(self.request, 'Job posted successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('gigs:detail', kwargs={'pk': self.object.pk})

class GigUpdateView(LoginRequiredMixin, UpdateView):
    model = Gig
    form_class = GigForm
    template_name = 'gigs/gig_form.html'

    def dispatch(self, request, *args, **kwargs):
        gig = self.get_object()
        if gig.homeowner != request.user:
            messages.error(request, 'You can only edit your own jobs.')
            return redirect('gigs:detail', pk=gig.pk)
        
        # Prevent editing of completed jobs
        if gig.job_status == 'completed':
            messages.error(request, 'Completed jobs cannot be edited.')
            return redirect('gigs:detail', pk=gig.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("=== POST METHOD CALLED ===")
        print(f"POST data: {dict(request.POST)}")
        
        self.object = self.get_object()
        form = self.get_form()
        
        # Debug: Check if form is valid
        if not form.is_valid():
            print(f"FORM INVALID: {form.errors}")
            return self.form_invalid(form)
        
        # Check for status change directly from POST
        post_status = request.POST.get('job_status')
        print(f"POST METHOD: job_status from POST: {post_status}")
        print(f"POST METHOD: Current gig status: {self.object.job_status}")
        
        # If status is being changed to completed, handle it specially
        if post_status == 'completed' and self.object.job_status != 'completed':
            print(f"POST METHOD: DETECTED COMPLETION - Processing invoice")
            return self.handle_job_completion(form)
        
        # Otherwise, process normally
        print("POST METHOD: Normal form processing")
        return self.form_valid(form)
    
    def handle_job_completion(self, form):
        gig = self.object
        print(f"HANDLE_COMPLETION: Starting process for gig {gig.pk}")
        
        # Validate hired provider
        if not gig.hired_provider:
            messages.error(self.request, 'This job has no hired provider. Cannot mark as complete.')
            return self.form_invalid(form)
        
        # Get accepted application
        try:
            accepted_application = JobApplication.objects.get(gig=gig, status='accepted')
        except JobApplication.DoesNotExist:
            messages.error(self.request, 'No accepted application found for this job.')
            return self.form_invalid(form)
        
        try:
            with transaction.atomic():
                # Update gig status
                gig.job_status = 'completed'
                gig.save()
                
                # Check if job is disputed - don't create order for disputed jobs
                if gig.job_status == 'disputed':
                    messages.warning(self.request, 'Cannot create order for disputed job. Please resolve dispute first.')
                    return redirect('gigs:detail', pk=gig.pk)
                
                # Create order
                from orders.models import Order
                from datetime import datetime
                from .utils import generate_invoice_pdf
                
                order = Order.objects.create(
                    gig=gig,
                    homeowner=gig.homeowner,
                    service_provider=gig.hired_provider,
                    status='completed',
                    total_amount=accepted_application.proposed_rate,
                    created_at=datetime.now(),
                    due_date=datetime.now(),
                    requirements=f"Job completed: {gig.title}"
                )
                
                # Generate invoice
                try:
                    invoice_path = generate_invoice_pdf(order, accepted_application)
                    messages.success(self.request, 'Job marked complete! Invoice generated.')
                    return redirect('reviews:create_review_with_invoice', 
                              user_id=gig.hired_provider.pk, 
                              order_id=order.pk,
                              job_id=gig.pk)
                except Exception as e:
                    messages.warning(self.request, f'Job complete but invoice failed: {e}')
                    return redirect('gigs:detail', pk=gig.pk)
                    
        except Exception as e:
            messages.error(self.request, f'Failed to complete job: {e}')
            return self.form_invalid(form)

    def form_valid(self, form):
        print(f"FORM_VALID: Regular update processing")
        messages.success(self.request, 'Job updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('gigs:detail', kwargs={'pk': self.object.pk})

class GigDeleteView(LoginRequiredMixin, DeleteView):
    model = Gig
    template_name = 'gigs/gig_confirm_delete.html'
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        gig = self.get_object()
        if gig.homeowner != request.user:
            messages.error(request, 'You can only delete your own jobs.')
            return redirect('gigs:detail', pk=gig.pk)
        
        # Prevent deletion of accepted and completed jobs
        if gig.job_status in ['accepted', 'completed']:
            status_name = 'accepted' if gig.job_status == 'accepted' else 'completed'
            messages.error(request, f'{status_name.title()} jobs cannot be deleted.')
            return redirect('gigs:detail', pk=gig.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Job deleted successfully!')
        return super().delete(request, *args, **kwargs)

# Function-based views
@login_required
def update_job_status(request, pk):
    """Update job status to complete or in_dispute with invoice generation"""
    gig = get_object_or_404(Gig, pk=pk)
    
    # Check if user owns the job
    if gig.homeowner != request.user:
        messages.error(request, 'You can only update your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    # Check if job can be marked as complete (accepted or active status)
    if gig.job_status not in ['accepted', 'active']:
        messages.error(request, 'Only accepted or active jobs can be marked as complete.')
        return redirect('gigs:detail', pk=pk)
    
    # Get the accepted application - try multiple approaches
    accepted_application = None
    try:
        # First try with hired_provider
        accepted_application = JobApplication.objects.get(gig=gig, status='accepted', service_provider=gig.hired_provider)
        print(f"DEBUG: Found accepted application with hired_provider")
    except JobApplication.DoesNotExist:
        try:
            # Fallback: get any accepted application for this gig
            accepted_application = JobApplication.objects.get(gig=gig, status='accepted')
            print(f"DEBUG: Found accepted application without hired_provider filter")
        except JobApplication.DoesNotExist:
            # Check if this job was created through estimate workflow
            # If no formal accepted application, check if hired_provider exists and allow completion
            if gig.hired_provider:
                print(f"DEBUG: No formal accepted app, but hired provider exists - allowing completion")
                # Create a dummy accepted application for completion process
                from .forms import JobApplicationForm
                accepted_application = JobApplication(
                    gig=gig,
                    service_provider=gig.hired_provider,
                    status='accepted',
                    proposed_rate=gig.budget_max,  # Use budget as fallback rate
                    cover_letter="Job accepted through estimate workflow"
                )
                print(f"DEBUG: Created dummy accepted application for completion")
            else:
                messages.error(request, 'This job has no hired provider. Cannot update project status.')
                return redirect('gigs:detail', pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['completed', 'in_dispute']:
            from django.db import transaction
            from orders.models import Order
            from datetime import datetime
            from .utils import generate_invoice_pdf
            
            with transaction.atomic():
                # Update job status
                gig.job_status = new_status
                gig.save()
                
                # Check if job is disputed - don't create order for disputed jobs
                if gig.job_status == 'disputed':
                    messages.warning(request, 'Cannot create order for disputed job. Please resolve dispute first.')
                    return redirect('gigs:detail', pk=pk)
                
                # Create order record for payment processing
                order = Order.objects.create(
                    gig=gig,
                    homeowner=gig.homeowner,
                    service_provider=gig.hired_provider,
                    status='completed' if new_status == 'completed' else 'disputed',
                    total_amount=accepted_application.proposed_rate,  # Use proposed rate from accepted application
                    created_at=datetime.now(),
                    due_date=datetime.now(),  # Set due date to now for completed jobs
                    requirements=f"Job completed: {gig.title}"
                )
                
                # Generate PDF invoice if job is completed
                if new_status == 'completed':
                    print(f"DEBUG: Starting invoice generation for order {order.pk}")
                    try:
                        invoice_path = generate_invoice_pdf(order, accepted_application)
                        print(f"DEBUG: Invoice generated successfully at: {invoice_path}")
                        messages.success(request, f'Job marked as complete. Invoice generated successfully. Please rate the service provider.')
                    except Exception as e:
                        print(f"DEBUG: Invoice generation failed: {str(e)}")
                        messages.warning(request, f'Job marked as complete, but invoice generation failed: {str(e)}. Please rate the service provider.')
                    
                    return redirect('reviews:create_review_with_invoice', 
                              user_id=gig.hired_provider.pk, 
                              order_id=order.pk,
                              job_id=gig.pk)
                elif new_status == 'in_dispute':
                    messages.warning(request, 'Job dispute reported. Administrators have been notified.')
                    return redirect('gigs:detail', pk=pk)
    
    # Show confirmation page
    context = {
        'gig': gig,
        'service_provider': gig.hired_provider,
        'accepted_application': accepted_application,
        'proposed_amount': accepted_application.proposed_rate
    }
    return render(request, 'gigs/update_job_status.html', context)

@login_required
def my_gigs(request):
    """Display gigs posted by the current user"""
    gigs = Gig.objects.filter(homeowner=request.user).select_related('category', 'hired_provider')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    date_filter = request.GET.get('date', '')
    sort_by = request.GET.get('sort', 'created_desc')
    
    # Apply search filter
    if search_query:
        gigs = gigs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            gigs = gigs.filter(is_active=True, hired_provider__isnull=True)
        elif status_filter == 'hired':
            gigs = gigs.filter(hired_provider__isnull=False)
        elif status_filter == 'completed':
            gigs = gigs.filter(job_status='completed')
        elif status_filter == 'inactive':
            gigs = gigs.filter(is_active=False)
    
    # Apply category filter
    if category_filter:
        gigs = gigs.filter(category__name=category_filter)
    
    # Apply date filter
    if date_filter:
        from datetime import timedelta
        now = timezone.now()
        
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            gigs = gigs.filter(created_at__gte=start_date)
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
            gigs = gigs.filter(created_at__gte=start_date)
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            gigs = gigs.filter(created_at__gte=start_date)
        elif date_filter == 'year':
            start_date = now - timedelta(days=365)
            gigs = gigs.filter(created_at__gte=start_date)
    
    # Apply sorting
    if sort_by == 'created_asc':
        gigs = gigs.order_by('created_at')
    elif sort_by == 'title_asc':
        gigs = gigs.order_by('title')
    elif sort_by == 'title_desc':
        gigs = gigs.order_by('-title')
    elif sort_by == 'budget_high':
        gigs = gigs.order_by('-budget_max')
    elif sort_by == 'budget_low':
        gigs = gigs.order_by('budget_min')
    else:  # created_desc (default)
        gigs = gigs.order_by('-created_at')
    
    # Calculate statistics
    total_gigs = gigs.count()
    active_gigs = gigs.filter(is_active=True, hired_provider__isnull=True).count()
    hired_gigs = gigs.filter(hired_provider__isnull=False).count()
    completed_gigs = gigs.filter(job_status='completed').count()
    
    context = {
        'gigs': gigs,
        'total_gigs': total_gigs,
        'active_gigs': active_gigs,
        'hired_gigs': hired_gigs,
        'completed_gigs': completed_gigs,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
        'categories': Category.objects.all(),
    }
    
    return render(request, 'gigs/my_gigs.html', context)

@login_required
def toggle_gig_status(request, pk):
    """Toggle gig active/inactive status"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'You can only modify your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    gig.is_active = not gig.is_active
    gig.save()
    
    status = 'activated' if gig.is_active else 'deactivated'
    messages.success(request, f'Job {status} successfully.')
    return redirect('gigs:my_gigs')

@login_required
def gig_analytics(request, pk):
    """Show analytics for a gig"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'You can only view analytics for your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    # Calculate analytics
    total_applications = JobApplication.objects.filter(gig=gig).count()
    pending_applications = JobApplication.objects.filter(gig=gig, status='pending').count()
    accepted_applications = JobApplication.objects.filter(gig=gig, status='accepted').count()
    
    context = {
        'gig': gig,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
    }
    return render(request, 'gigs/gig_analytics.html', context)

def category_gigs(request, name):
    """Display gigs by category"""
    # Semantic mapping for common terms
    semantic_mappings = {
        'electrician': 'Electrical',
        'electric': 'Electrical',
        'electricity': 'Electrical',
        'plumber': 'Plumbing',
        'plumbing': 'Plumbing',
        'construction': 'Construction',
        'builder': 'Construction',
        'building': 'Construction',
        'hvac': 'HVAC',
        'aircon': 'HVAC',
        'air conditioning': 'HVAC',
        'landscaping': 'Landscaping',
        'gardener': 'Landscaping',
        'garden': 'Landscaping',
        'cleaning': 'Cleaning',
        'cleaner': 'Cleaning',
        'automotive': 'Automotive',
        'car': 'Automotive',
        'mechanic': 'Automotive',
        'technology': 'Technology',
        'tech': 'Technology',
        'it': 'Technology',
        'painting': 'Painting',
        'painter': 'Painting',
        'appliance': 'Appliance Repair',
        'appliances': 'Appliance Repair',
    }
    
    # Try exact match first, then semantic mapping, then case-insensitive, then partial match
    category = None
    
    # Try exact match
    try:
        category = Category.objects.get(name=name)
    except Category.DoesNotExist:
        # Try semantic mapping
        semantic_match = semantic_mappings.get(name.lower())
        if semantic_match:
            try:
                category = Category.objects.get(name=semantic_match)
            except Category.DoesNotExist:
                pass
        
        # If still no category, try case-insensitive match
        if not category:
            try:
                category = Category.objects.get(name__iexact=name)
            except Category.DoesNotExist:
                # Try partial match (contains)
                categories = Category.objects.filter(name__icontains=name)
                if categories.exists():
                    category = categories.first()
                else:
                    # If still no match, try to find by slug-like matching
                    slug_search = name.replace('-', ' ')
                    category = Category.objects.filter(name__icontains=slug_search).first()
    
    # If still no category found, return 404
    if not category:
        from django.http import Http404
        raise Http404(f"No Category matches the given query: {name}")
    
    gigs = Gig.objects.filter(category=category, is_active=True, hired_provider__isnull=True).order_by('-created_at')
    
    return render(request, 'gigs/category_gigs.html', {
        'category': category,
        'gigs': gigs
    })

def service_providers(request):
    """Display all service providers"""
    from reviews.models import Review
    from django.db.models import Avg, Count
    
    providers = User.objects.filter(user_type='service_provider').annotate(
        avg_rating=Avg('reviews_received__rating', default=0),
        total_reviews=Count('reviews_received'),
        completed_jobs=Count('hired_jobs', filter=Q(hired_jobs__job_status='completed'))
    )
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    rating_filter = request.GET.get('rating', '')
    sort_by = request.GET.get('sort', 'rating_desc')
    
    # Apply search filter
    if search_query:
        providers = providers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__bio__icontains=search_query) |
            Q(profile__skills__icontains=search_query)
        )
    
    # Apply rating filter
    if rating_filter:
        min_rating = float(rating_filter)
        providers = providers.filter(avg_rating__gte=min_rating)
    
    # Apply sorting
    if sort_by == 'rating_asc':
        providers = providers.order_by('avg_rating')
    elif sort_by == 'rating_desc':
        providers = providers.order_by('-avg_rating')
    elif sort_by == 'reviews_asc':
        providers = providers.order_by('total_reviews')
    elif sort_by == 'reviews_desc':
        providers = providers.order_by('-total_reviews')
    elif sort_by == 'jobs_asc':
        providers = providers.order_by('completed_jobs')
    elif sort_by == 'jobs_desc':
        providers = providers.order_by('-completed_jobs')
    elif sort_by == 'name_asc':
        providers = providers.order_by('first_name', 'last_name')
    elif sort_by == 'name_desc':
        providers = providers.order_by('-first_name', '-last_name')
    else:  # rating_desc (default)
        providers = providers.order_by('-avg_rating')
    
    # Calculate statistics
    total_providers = providers.count()
    avg_rating_all = providers.aggregate(avg=Avg('avg_rating'))['avg'] or 0
    top_rated = providers.filter(avg_rating__gte=4.5).count()
    
    context = {
        'providers': providers,
        'total_providers': total_providers,
        'avg_rating_all': avg_rating_all,
        'top_rated': top_rated,
        'search_query': search_query,
        'rating_filter': rating_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'gigs/service_providers.html', context)

@login_required
def accept_job(request, pk):
    """Accept a job application"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'You can only accept applications for your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    # Get application_id from either GET or POST
    application_id = request.GET.get('application_id') or request.POST.get('application_id')
    
    if not application_id:
        messages.error(request, 'Application ID is required.')
        return redirect('gigs:detail', pk=pk)
    
    application = get_object_or_404(JobApplication, pk=application_id, gig=gig)
    
    with transaction.atomic():
        # Update application status
        application.status = 'accepted'
        application.save()
        
        # Update gig status and hired provider
        gig.job_status = 'accepted'
        gig.hired_provider = application.service_provider
        gig.save()
        
        # Reject other applications
        JobApplication.objects.filter(gig=gig).exclude(pk=application_id).update(status='rejected')
    
    messages.success(request, 'Job application accepted successfully!')
    return redirect('gigs:detail', pk=pk)

@login_required
def reject_job(request, pk):
    """Reject a job application"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'You can only reject applications for your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    application_id = request.POST.get('application_id')
    application = get_object_or_404(JobApplication, pk=application_id, gig=gig)
    
    application.status = 'rejected'

def my_provider_jobs(request):
    """Display jobs hired for the current service provider"""
    from orders.models import Order, JobOffer
    
    # Method 1: Jobs where provider is directly hired (hired_provider field)
    hired_provider_jobs = Gig.objects.filter(
        hired_provider=request.user
    ).select_related('homeowner')
    
    # Method 2: Jobs where provider has accepted applications
    accepted_applications = JobApplication.objects.filter(
        service_provider=request.user,
        status='accepted'
    ).select_related('gig', 'gig__homeowner')
    application_jobs = [app.gig for app in accepted_applications]
    
    # Method 3: Jobs where provider has approved job offers
    approved_offers = JobOffer.objects.filter(
        service_provider=request.user,
        status='approved'
    ).select_related('gig', 'gig__homeowner')
    offer_jobs = [offer.gig for offer in approved_offers if offer.gig]
    
    # Method 4: Jobs where provider is assigned through orders
    order_jobs = []
    for order in Order.objects.filter(service_provider=request.user).select_related('gig', 'gig__homeowner'):
        if order.gig:
            order_jobs.append(order.gig)
    
    # Combine all job sources and remove duplicates
    all_jobs = []
    seen_gigs = set()
    
    # Add hired provider jobs
    for job in hired_provider_jobs:
        if job.pk not in seen_gigs:
            job.source = 'direct'
            all_jobs.append(job)
            seen_gigs.add(job.pk)
    
    # Add application jobs
    for job in application_jobs:
        if job.pk not in seen_gigs:
            job.source = 'application'
            all_jobs.append(job)
            seen_gigs.add(job.pk)
    
    # Add offer jobs
    for job in offer_jobs:
        if job.pk not in seen_gigs:
            job.source = 'offer'
            all_jobs.append(job)
            seen_gigs.add(job.pk)
    
    # Add order jobs
    for job in order_jobs:
        if job.pk not in seen_gigs:
            job.source = 'order'
            all_jobs.append(job)
            seen_gigs.add(job.pk)
    
    # Sort all jobs by creation date
    all_jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    sort_by = request.GET.get('sort', 'created_desc')
    
    # Apply search filter
    if search_query:
        all_jobs = [
            job for job in all_jobs 
            if search_query.lower() in job.title.lower() or 
               search_query.lower() in job.description.lower() or
               (job.location and search_query.lower() in job.location.lower())
        ]
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            all_jobs = [job for job in all_jobs if job.job_status in ['accepted', 'active']]
        elif status_filter == 'completed':
            all_jobs = [job for job in all_jobs if job.job_status == 'completed']
        elif status_filter == 'pending':
            all_jobs = [job for job in all_jobs if job.job_status == 'pending']
        elif status_filter == 'private':
            all_jobs = [job for job in all_jobs if job.is_private]
        elif status_filter == 'public':
            all_jobs = [job for job in all_jobs if not job.is_private]
    
    # Apply date filter
    if date_filter:
        from datetime import datetime, timedelta
        now = timezone.now()
        
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            all_jobs = [job for job in all_jobs if job.created_at >= start_date]
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
            all_jobs = [job for job in all_jobs if job.created_at >= start_date]
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            all_jobs = [job for job in all_jobs if job.created_at >= start_date]
        elif date_filter == 'year':
            start_date = now - timedelta(days=365)
            all_jobs = [job for job in all_jobs if job.created_at >= start_date]
    
    # Apply sorting
    if sort_by == 'created_asc':
        all_jobs.sort(key=lambda x: x.created_at)
    elif sort_by == 'title_asc':
        all_jobs.sort(key=lambda x: x.title.lower())
    elif sort_by == 'title_desc':
        all_jobs.sort(key=lambda x: x.title.lower(), reverse=True)
    elif sort_by == 'budget_high':
        all_jobs.sort(key=lambda x: (x.budget_max or x.budget_min or 0), reverse=True)
    elif sort_by == 'budget_low':
        all_jobs.sort(key=lambda x: (x.budget_min or x.budget_max or 999999))
    else:  # created_desc (default)
        all_jobs.sort(key=lambda x: x.created_at, reverse=True)
    
    # Calculate statistics
    total_jobs = len(all_jobs)
    active_count = len([job for job in all_jobs if job.job_status in ['accepted', 'active']])
    completed_count = len([job for job in all_jobs if job.job_status == 'completed'])
    private_count = len([job for job in all_jobs if job.is_private])
    
    context = {
        'jobs': all_jobs,
        'total_jobs': total_jobs,
        'active_count': active_count,
        'completed_count': completed_count,
        'private_count': private_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'gigs/my_provider_jobs.html', context)

@login_required
def my_jobs(request):
    """Display jobs posted by the current user"""
    jobs = Gig.objects.filter(homeowner=request.user).select_related('category', 'hired_provider')
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    date_filter = request.GET.get('date', '')
    sort_by = request.GET.get('sort', 'created_desc')
    
    # Apply search filter
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        if status_filter == 'pending':
            jobs = jobs.filter(job_status='pending')
        elif status_filter == 'accepted':
            jobs = jobs.filter(job_status='accepted')
        elif status_filter == 'active':
            jobs = jobs.filter(job_status='active')
        elif status_filter == 'completed':
            jobs = jobs.filter(job_status='completed')
        elif status_filter == 'cancelled':
            jobs = jobs.filter(job_status='cancelled')
    
    # Apply category filter
    if category_filter:
        jobs = jobs.filter(category__name=category_filter)
    
    # Apply date filter
    if date_filter:
        from datetime import timedelta
        now = timezone.now()
        
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            jobs = jobs.filter(created_at__gte=start_date)
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
            jobs = jobs.filter(created_at__gte=start_date)
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            jobs = jobs.filter(created_at__gte=start_date)
        elif date_filter == 'year':
            start_date = now - timedelta(days=365)
            jobs = jobs.filter(created_at__gte=start_date)
    
    # Apply sorting
    if sort_by == 'created_asc':
        jobs = jobs.order_by('created_at')
    elif sort_by == 'title_asc':
        jobs = jobs.order_by('title')
    elif sort_by == 'title_desc':
        jobs = jobs.order_by('-title')
    elif sort_by == 'budget_high':
        jobs = jobs.order_by('-budget_max')
    elif sort_by == 'budget_low':
        jobs = jobs.order_by('budget_min')
    else:  # created_desc (default)
        jobs = jobs.order_by('-created_at')
    
    # Calculate statistics
    total_jobs = jobs.count()
    pending_jobs = jobs.filter(job_status='pending').count()
    active_jobs = jobs.filter(job_status='active').count()
    completed_jobs = jobs.filter(job_status='completed').count()
    
    context = {
        'jobs': jobs,
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
        'categories': Category.objects.all(),
    }
    
    return render(request, 'gigs/my_jobs.html', context)

@login_required
def create_quotation_request(request):
    """Create a new quotation request with multiple provider selection"""
    if request.user.user_type != 'homeowner':
        messages.error(request, 'Only homeowners can create quotation requests.')
        return redirect('home')
    
    if request.method == 'POST':
        form = QuotationRequestWithProvidersForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create quotation request
                quotation = form.save(commit=False)
                quotation.homeowner = request.user
                quotation.status = 'receiving_responses'
                quotation.save()
                
                # Get selected providers
                selected_providers = form.cleaned_data['providers']
                
                # Create QuotationRequestProvider records for each selected provider
                for provider in selected_providers:
                    QuotationRequestProvider.objects.create(
                        quotation_request=quotation,
                        service_provider=provider
                    )
                    
                    # Send interactive WhatsApp notification
                    if provider.phone:
                        from whatsapp_quotation_flow import get_whatsapp_quotation_flow
                        whatsapp_flow = get_whatsapp_quotation_flow()
                        result = whatsapp_flow.send_interactive_quotation_request(
                            to=provider.phone,
                            quotation=quotation,
                            provider=provider
                        )
                        
                        # Log the result
                        import logging
                        logger = logging.getLogger(__name__)
                        if result['success']:
                            service_used = result.get('service_used', 'unknown')
                            if result.get('interactive_sent'):
                                logger.info(f"Interactive WhatsApp notification sent to {provider.email}")
                            else:
                                logger.info(f"Notification sent to {provider.email} via {service_used}")
                        else:
                            logger.error(f"Notification failed for {provider.email}: {result.get('error')}")
                            
                    else:
                        # Handle missing phone number
                        from phone_status_system import PhoneStatusSystem, PhoneStatus
                        phone_status, status_msg = PhoneStatusSystem.get_phone_status(provider)
                        if phone_status == PhoneStatus.MISSING:
                            from phone_status_system import handle_phone_issue
                            handle_result = handle_phone_issue(provider, phone_status, context='quotation_request')
                            logger.info(f"Phone issue handled for {provider.email}: {handle_result}")
                
                messages.success(request, f'Quotation request sent to {len(selected_providers)} service providers!')
                return redirect('gigs:quotation_detail', pk=quotation.pk)
    else:
        form = QuotationRequestWithProvidersForm()
    
    return render(request, 'gigs/quotation_request_form.html', {'form': form})

@login_required
def quotation_detail(request, pk):
    """Display quotation request details"""
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    responses = QuotationResponse.objects.filter(quotation_request=quotation).select_related('service_provider')
    
    # Check if user can view this quotation
    if request.user != quotation.homeowner:
        # Only service providers can view other people's quotations (if they were sent the request)
        if request.user.user_type == 'service_provider':
            # Check if this provider was sent the request
            was_sent = QuotationRequestProvider.objects.filter(
                quotation_request=quotation,
                service_provider=request.user
            ).exists()
            
            if not was_sent:
                print(f"DEBUG: Unauthorized access attempt by {request.user} to view quotation {quotation.pk}")
                messages.error(request, 'You can only view quotation requests that were sent to you.')
                return redirect('home')
        else:
            # Non-homeowner, non-service-provider users cannot access other people's quotations
            print(f"DEBUG: Unauthorized access attempt by {request.user} to view quotation {quotation.pk}")
            messages.error(request, 'You can only view your own quotation requests.')
            return redirect('home')
    
    # Close all expired quotations (including this one if needed)
    close_expired_quotations()
    
    # Refresh the quotation object in case its status was updated
    quotation.refresh_from_db()
    
    # Check if deadline has passed and update status
    if quotation.status == 'receiving_responses' and quotation.is_response_deadline_passed():
        quotation.status = 'evaluation_period'
        quotation.save()
    
    # Get all providers who were sent this quotation request
    sent_providers = QuotationRequestProvider.objects.filter(
        quotation_request=quotation
    ).select_related('service_provider').order_by('service_provider__email')
    
    # Create a dictionary to track response status for each provider
    providers_with_status = []
    for sent_provider in sent_providers:
        provider = sent_provider.service_provider
        response = responses.filter(service_provider=provider).first()
        
        providers_with_status.append({
            'provider': provider,
            'sent_at': sent_provider.sent_at,
            'response': response,
            'status': response.status if response else 'not_responded'
        })
    
    return render(request, 'gigs/quotation_detail.html', {
        'quotation': quotation,
        'responses': responses,
        'providers_with_status': providers_with_status
    })

@login_required
def respond_to_quotation(request, pk):
    """Respond to a quotation request"""
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    
    # Close all expired quotations first
    close_expired_quotations()
    
    # Refresh the quotation object in case its status was updated
    quotation.refresh_from_db()
    
    # Check if user is a service provider
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Only service providers can respond to quotation requests.')
        return redirect('gigs:detail', pk=pk)
    
    # Check if quotation can still receive responses
    if not quotation.can_receive_responses():
        if quotation.status == 'evaluation_period':
            messages.error(request, 'The response deadline has passed and this quotation is now in evaluation period. You can no longer submit a quote.')
        else:
            messages.error(request, 'This quotation request is no longer accepting responses.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    # Check if user has already responded
    existing_response = QuotationResponse.objects.filter(
        quotation_request=quotation,
        service_provider=request.user
    ).first()
    
    if existing_response:
        messages.error(request, 'You have already submitted a response to this quotation request.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    if request.method == 'POST':
        form = QuotationResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.quotation_request = quotation
            response.service_provider = request.user
            response.save()
            messages.success(request, 'Quotation response submitted successfully!')
            return redirect('gigs:quotation_detail', pk=pk)
    else:
        form = QuotationResponseForm()
    
    return render(request, 'gigs/quotation_response_form.html', {
        'form': form,
        'quotation': quotation
    })

@login_required
def select_quotation(request, pk, response_id):
    """Select a quotation response and create private job"""
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    
    if quotation.homeowner != request.user:
        messages.error(request, 'You can only select responses for your own quotations.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    response = get_object_or_404(QuotationResponse, pk=response_id, quotation_request=quotation)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Update quotation status
            quotation.status = 'provider_selected'
            quotation.selected_provider = response.service_provider
            quotation.save()
            
            # Update response status
            response.status = 'accepted'
            response.save()
            
            # Reject other responses
            QuotationResponse.objects.filter(quotation_request=quotation).exclude(pk=response_id).update(status='rejected')
            
            # Create a private job from the selected quotation
            gig = Gig.objects.create(
                homeowner=quotation.homeowner,
                title=quotation.title,
                description=quotation.description,
                category=quotation.category,
                location=quotation.location,
                start_date=quotation.start_date,
                end_date=quotation.end_date,
                budget_min=response.estimated_price,
                budget_max=response.estimated_price,
                urgency=quotation.urgency,
                is_private=True,
                hired_provider=response.service_provider,
                job_status='accepted'
            )
            
            messages.success(request, f'Provider selected and private job created successfully! Job ID: {gig.pk}')
            return redirect('gigs:detail', pk=gig.pk)
    
    # Show confirmation page
    return render(request, 'gigs/select_quotation.html', {
        'quotation': quotation,
        'response': response
    })

@login_required
def reject_quotation(request, pk, response_id):
    """Reject a quotation response"""
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    
    if quotation.homeowner != request.user:
        messages.error(request, 'You can only reject responses for your own quotations.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    response = get_object_or_404(QuotationResponse, pk=response_id, quotation_request=quotation)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Update response status
            response.status = 'rejected'
            response.save()
            
            messages.success(request, 'Quotation response rejected successfully.')
            return redirect('gigs:quotation_detail', pk=pk)
    
    # Show confirmation page
    return render(request, 'gigs/reject_quotation.html', {
        'quotation': quotation,
        'response': response
    })

@login_required
def update_quotation(request, pk):
    """Update an existing quotation request"""
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    
    # Only homeowners can update their own quotations
    if quotation.homeowner != request.user:
        messages.error(request, 'You can only update your own quotation requests.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    # Check if quotation can be updated (not already selected or completed)
    if quotation.status in ['provider_selected', 'completed']:
        messages.error(request, 'This quotation cannot be updated as it has already been processed.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    # Check if there are already responses
    responses_count = QuotationResponse.objects.filter(quotation_request=quotation).count()
    if responses_count > 0:
        messages.error(request, 'This quotation cannot be updated as it has already received responses.')
        return redirect('gigs:quotation_detail', pk=pk)
    
    if request.method == 'POST':
        form = UpdateQuotationRequestForm(request.POST, instance=quotation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quotation request updated successfully!')
            return redirect('gigs:quotation_detail', pk=pk)
    else:
        form = UpdateQuotationRequestForm(instance=quotation)
    
    return render(request, 'gigs/update_quotation.html', {
        'form': form,
        'quotation': quotation
    })

@login_required
def my_quotations(request):
    """Display user's quotation requests or quotations sent to service providers"""
    # Close all expired quotations first
    close_expired_quotations()
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    sort_by = request.GET.get('sort', 'created_desc')
    
    if request.user.user_type == 'homeowner':
        # Homeowners see quotation requests they created
        quotations = QuotationRequest.objects.filter(homeowner=request.user).select_related('category')
        user_type = 'homeowner'
        
        # Apply search filter
        if search_query:
            quotations = quotations.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        # Apply status filter
        if status_filter:
            quotations = quotations.filter(status=status_filter)
        
        # Apply date filter
        if date_filter:
            from datetime import timedelta
            now = timezone.now()
            
            if date_filter == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                quotations = quotations.filter(created_at__gte=start_date)
            elif date_filter == 'week':
                start_date = now - timedelta(days=7)
                quotations = quotations.filter(created_at__gte=start_date)
            elif date_filter == 'month':
                start_date = now - timedelta(days=30)
                quotations = quotations.filter(created_at__gte=start_date)
            elif date_filter == 'year':
                start_date = now - timedelta(days=365)
                quotations = quotations.filter(created_at__gte=start_date)
        
        # Apply sorting
        if sort_by == 'created_asc':
            quotations = quotations.order_by('created_at')
        elif sort_by == 'deadline_asc':
            quotations = quotations.order_by('response_deadline')
        elif sort_by == 'deadline_desc':
            quotations = quotations.order_by('-response_deadline')
        elif sort_by == 'title_asc':
            quotations = quotations.order_by('title')
        elif sort_by == 'title_desc':
            quotations = quotations.order_by('-title')
        else:  # created_desc
            quotations = quotations.order_by('-created_at')
        
        # Calculate statistics
        total_quotations = quotations.count()
        pending_quotations = quotations.filter(status='receiving_responses').count()
        evaluation_quotations = quotations.filter(status='evaluation_period').count()
        selected_quotations = quotations.filter(status='provider_selected').count()
        
    else:
        # Service providers only see quotation requests where they are selected to provide quotes
        received_quotations = QuotationRequestProvider.objects.filter(
            service_provider=request.user
        ).select_related('quotation_request', 'quotation_request__homeowner', 'quotation_request__category').order_by('-sent_at')
        
        # Convert to quotation request objects for template compatibility
        quotations = []
        for received_quotation in received_quotations:
            quotation = received_quotation.quotation_request
            
            # Only show quotations that are in active status and where this provider can respond
            if quotation.status in ['receiving_responses', 'evaluation_period']:
                quotation.provider_response = QuotationResponse.objects.filter(
                    quotation_request=quotation,
                    service_provider=request.user
                ).first()
                quotations.append(quotation)
            elif quotation.selected_provider == request.user:
                quotation.provider_response = QuotationResponse.objects.filter(
                    quotation_request=quotation,
                    service_provider=request.user
                ).first()
                quotations.append(quotation)
        
        # Apply search filter
        if search_query:
            quotations = [
                q for q in quotations 
                if search_query.lower() in q.title.lower() or 
                   search_query.lower() in q.description.lower() or
                   (q.location and search_query.lower() in q.location.lower()) or
                   (q.homeowner.get_full_name() and search_query.lower() in q.homeowner.get_full_name().lower()) or
                   search_query.lower() in q.homeowner.email.lower()
            ]
        
        # Apply status filter
        if status_filter:
            quotations = [q for q in quotations if q.status == status_filter]
        
        # Apply date filter
        if date_filter:
            from datetime import timedelta
            now = timezone.now()
            
            if date_filter == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                quotations = [q for q in quotations if q.created_at.date() >= start_date.date()]
            elif date_filter == 'week':
                start_date = now - timedelta(days=7)
                quotations = [q for q in quotations if q.created_at >= start_date]
            elif date_filter == 'month':
                start_date = now - timedelta(days=30)
                quotations = [q for q in quotations if q.created_at >= start_date]
            elif date_filter == 'year':
                start_date = now - timedelta(days=365)
                quotations = [q for q in quotations if q.created_at >= start_date]
        
        # Apply sorting
        if sort_by == 'created_asc':
            quotations.sort(key=lambda x: x.created_at)
        elif sort_by == 'deadline_asc':
            quotations.sort(key=lambda x: x.response_deadline or timezone.now())
        elif sort_by == 'deadline_desc':
            quotations.sort(key=lambda x: x.response_deadline or timezone.min, reverse=True)
        elif sort_by == 'title_asc':
            quotations.sort(key=lambda x: x.title.lower())
        elif sort_by == 'title_desc':
            quotations.sort(key=lambda x: x.title.lower(), reverse=True)
        else:  # created_desc
            quotations.sort(key=lambda x: x.created_at, reverse=True)
        
        # Calculate statistics
        total_quotations = len(quotations)
        pending_quotations = len([q for q in quotations if q.status == 'receiving_responses'])
        evaluation_quotations = len([q for q in quotations if q.status == 'evaluation_period'])
        selected_quotations = len([q for q in quotations if q.status == 'provider_selected'])
        
        user_type = 'service_provider'
    
    context = {
        'quotations': quotations,
        'user_type': user_type,
        'total_quotations': total_quotations,
        'pending_quotations': pending_quotations,
        'evaluation_quotations': evaluation_quotations,
        'selected_quotations': selected_quotations,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'gigs/my_quotations.html', context)

@login_required
def provider_quotations(request):
    """Display quotation requests sent to this service provider"""
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Only service providers can view received quotation requests.')
        return redirect('home')
    
    # Get all quotation requests sent to this provider
    received_quotations = list(QuotationRequestProvider.objects.filter(
        service_provider=request.user
    ).select_related('quotation_request', 'quotation_request__homeowner', 'quotation_request__category').order_by('-sent_at'))
    
    # Get filter parameters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    sort_by = request.GET.get('sort', 'sent_desc')
    
    # Apply search filter
    if search_query:
        received_quotations = [
            rq for rq in received_quotations 
            if search_query.lower() in rq.quotation_request.title.lower() or 
               search_query.lower() in rq.quotation_request.description.lower() or
               (rq.quotation_request.location and search_query.lower() in rq.quotation_request.location.lower()) or
               (rq.quotation_request.homeowner.get_full_name() and search_query.lower() in rq.quotation_request.homeowner.get_full_name().lower()) or
               search_query.lower() in rq.quotation_request.homeowner.email.lower() or
               (rq.quotation_request.category and search_query.lower() in rq.quotation_request.category.name.lower())
        ]
    
    # Apply status filter
    if status_filter:
        received_quotations = [
            rq for rq in received_quotations 
            if rq.quotation_request.status == status_filter
        ]
    
    # Apply date filter
    if date_filter:
        from datetime import timedelta
        now = timezone.now()
        
        if date_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            received_quotations = [rq for rq in received_quotations if rq.sent_at.date() >= start_date.date()]
        elif date_filter == 'week':
            start_date = now - timedelta(days=7)
            received_quotations = [rq for rq in received_quotations if rq.sent_at >= start_date]
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            received_quotations = [rq for rq in received_quotations if rq.sent_at >= start_date]
        elif date_filter == 'year':
            start_date = now - timedelta(days=365)
            received_quotations = [rq for rq in received_quotations if rq.sent_at >= start_date]
    
    # Apply sorting
    if sort_by == 'sent_asc':
        received_quotations.sort(key=lambda x: x.sent_at)
    elif sort_by == 'deadline_asc':
        received_quotations.sort(key=lambda x: x.quotation_request.response_deadline or timezone.now())
    elif sort_by == 'deadline_desc':
        received_quotations.sort(key=lambda x: x.quotation_request.response_deadline or timezone.min, reverse=True)
    elif sort_by == 'title_asc':
        received_quotations.sort(key=lambda x: x.quotation_request.title.lower())
    elif sort_by == 'title_desc':
        received_quotations.sort(key=lambda x: x.quotation_request.title.lower(), reverse=True)
    else:  # sent_desc (default)
        received_quotations.sort(key=lambda x: x.sent_at, reverse=True)
    
    # Calculate statistics
    total_quotations = len(received_quotations)
    pending_count = len([rq for rq in received_quotations if rq.quotation_request.status == 'receiving_responses'])
    evaluation_count = len([rq for rq in received_quotations if rq.quotation_request.status == 'evaluation_period'])
    selected_count = len([rq for rq in received_quotations if rq.quotation_request.status == 'provider_selected'])
    
    # Check which ones have user responses
    responded_count = 0
    for rq in received_quotations:
        if rq.quotation_request.responses.filter(service_provider=request.user).exists():
            responded_count += 1
    
    context = {
        'received_quotations': received_quotations,
        'total_quotations': total_quotations,
        'pending_count': pending_count,
        'evaluation_count': evaluation_count,
        'selected_count': selected_count,
        'responded_count': responded_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'gigs/provider_quotations.html', context)

@login_required
def apply_for_job(request, pk):
    """Apply for a job"""
    gig = get_object_or_404(Gig, pk=pk)
    
    # Check if user has already applied for this job
    existing_application = JobApplication.objects.filter(
        gig=gig, 
        service_provider=request.user
    ).first()
    
    if existing_application:
        messages.error(request, 'You have already applied for this job.')
        return redirect('gigs:detail', pk=pk)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.gig = gig
            application.service_provider = request.user
            application.save()
            
            # Send notification to job owner
            from notifications.services import NotificationService
            NotificationService.send_notification(
                recipient=gig.homeowner,
                notification_type='job_applied',
                title=f'New Job Application - {gig.title}',
                notification_message=f'{request.user.first_name} {request.user.last_name} has applied for your job: {gig.title}',
                sender=request.user,
                gig=gig,
                channels=['email', 'sms', 'whatsapp', 'in_app']
            )
            
            # Send WhatsApp notification directly
            try:
                from whatsapp_service import get_whatsapp_service
                whatsapp_service = get_whatsapp_service()
                
                # Check if homeowner has phone number
                if gig.homeowner.phone:
                    job_details = {
                        'title': gig.title,
                        'client_name': f"{gig.homeowner.first_name} {gig.homeowner.last_name}",
                        'budget': str(gig.budget),
                        'deadline': gig.deadline.strftime('%Y-%m-%d') if gig.deadline else 'Not specified'
                    }
                    
                    whatsapp_service.send_job_application_notification(
                        to=gig.homeowner.phone,
                        job_details=job_details
                    )
            except Exception as e:
                # Log error but don't fail the application process
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send WhatsApp notification for job application: {e}")
            
            messages.success(request, 'Job application submitted successfully!')
            return redirect('gigs:detail', pk=pk)
    else:
        form = JobApplicationForm()
    
    return render(request, 'gigs/apply_for_job.html', {
        'form': form,
        'gig': gig
    })

@login_required
def job_applications(request, pk):
    """Display applications for a job"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'You can only view applications for your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    applications = JobApplication.objects.filter(gig=gig).select_related('service_provider')
    return render(request, 'gigs/job_applications.html', {
        'gig': gig,
        'applications': applications
    })

@login_required
def update_application_status(request, pk):
    """Update job application status"""
    application = get_object_or_404(JobApplication, pk=pk)
    
    if application.gig.homeowner != request.user:
        messages.error(request, 'You can only update applications for your own jobs.')
        return redirect('gigs:detail', pk=application.gig.pk)
    
    new_status = request.POST.get('status')
    if new_status in ['pending', 'accepted', 'rejected']:
        application.status = new_status
        application.save()
        
        if new_status == 'accepted':
            # Update gig status
            application.gig.job_status = 'accepted'
            application.gig.hired_provider = application.service_provider
            application.gig.save()
            
            # Reject other applications
            JobApplication.objects.filter(gig=application.gig).exclude(pk=pk).update(status='rejected')
            
            # Send notification to selected provider
            from notifications.services import NotificationService
            NotificationService.send_notification(
                recipient=application.service_provider,
                notification_type='job_accepted',
                title=f'Job Application Accepted - {application.gig.title}',
                notification_message=f'Your application for {application.gig.title} has been accepted! Reply ACCEPT to confirm this job.',
                sender=request.user,
                gig=application.gig,
                channels=['email', 'sms', 'whatsapp', 'in_app']
            )
            
            messages.success(request, 'Application accepted and job assigned!')
        else:
            messages.success(request, f'Application status updated to {new_status}.')
    
    return redirect('gigs:job_applications', pk=application.gig.pk)

@login_required
def complete_job(request, pk):
    """Mark a job as complete"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'You can only complete your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    if gig.job_status != 'active':
        messages.error(request, 'Only active jobs can be marked as complete.')
        return redirect('gigs:detail', pk=pk)
    
    if request.method == 'POST':
        gig.job_status = 'completed'
        gig.save()
        
        # Check if job is disputed - don't create order for disputed jobs
        if gig.job_status == 'disputed':
            messages.warning(request, 'Cannot create order for disputed job. Please resolve dispute first.')
            return redirect('gigs:detail', pk=pk)
        
        # Create order record
        order = Order.objects.create(
            gig=gig,
            homeowner=gig.homeowner,
            service_provider=gig.hired_provider,
            status='completed',
            total_amount=gig.budget_max or gig.budget_min,
            created_at=datetime.now()
        )
        
        # Send notification to service provider
        from notifications.services import NotificationService
        NotificationService.send_notification(
            recipient=gig.hired_provider,
            notification_type='job_completed',
            title=f'Job Completed - {gig.title}',
            notification_message=f'The job {gig.title} has been marked as complete. Please wait for review.',
            sender=request.user,
            gig=gig,
            order=order,
            channels=['email', 'sms', 'whatsapp', 'in_app']
        )
        messages.success(request, 'Job marked as complete!')
        return redirect('reviews:create', order_id=order.pk)
    
    return render(request, 'gigs/complete_job.html', {'gig': gig})

@login_required
def view_invoice(request, pk):
    """View invoice for an order"""
    order = get_object_or_404(Order, pk=pk)
    
    if order.homeowner != request.user and order.service_provider != request.user:
        messages.error(request, 'You can only view invoices for your own orders.')
        return redirect('home')
    
    return render(request, 'gigs/invoice_detail.html', {'order': order})

@login_required
def leave_review(request, pk):
    """Leave a review for a completed job"""
    gig = get_object_or_404(Gig, pk=pk)
    
    if gig.homeowner != request.user:
        messages.error(request, 'Only the job owner can leave reviews.')
        return redirect('gigs:detail', pk=pk)
    
    if gig.job_status != 'completed':
        messages.error(request, 'You can only review completed jobs.')
        return redirect('gigs:detail', pk=pk)
    
    # Check if review already exists
    from reviews.models import Review
    existing_review = Review.objects.filter(
        order__gig=gig,
        client=request.user
    ).first()
    
    if existing_review:
        messages.info(request, 'You have already reviewed this job.')
        return redirect('reviews:detail', pk=existing_review.pk)
    
    return redirect('reviews:create', order_id=order.pk)