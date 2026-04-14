from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import os

from users.models import User
from .models_features import (
    EnhancedReview, PortfolioItem, AvailabilityCalendar, 
    AvailabilitySlot, Invoice, InvoiceItem, Dispute, 
    DisputeMessage, UserAnalytics
)
from gigs.models import Gig, Category
from orders.models import Order


# Portfolio Views
@login_required
def portfolio_list(request, user_id=None):
    """List portfolio items for a provider"""
    if user_id:
        provider = get_object_or_404(User, id=user_id, user_type='service_provider')
    else:
        provider = request.user
    
    portfolio_items = PortfolioItem.objects.filter(
        provider=provider,
        is_public=True
    ).select_related('category').order_by('-is_featured', 'sort_order', '-created_at')
    
    # Get provider stats
    stats = {
        'total_items': portfolio_items.count(),
        'featured_items': portfolio_items.filter(is_featured=True).count(),
        'categories': portfolio_items.values_list('category__name', flat=True).distinct(),
    }
    
    context = {
        'provider': provider,
        'portfolio_items': portfolio_items,
        'stats': stats,
        'is_own_portfolio': request.user == provider,
    }
    
    return render(request, 'core/portfolio/list.html', context)


class PortfolioCreateView(LoginRequiredMixin, CreateView):
    """Create new portfolio item"""
    model = PortfolioItem
    template_name = 'core/portfolio/create.html'
    fields = [
        'title', 'description', 'category', 'image', 'video',
        'project_date', 'location', 'budget', 'duration',
        'client_name', 'client_testimonial',
        'before_image', 'after_image', 'tags', 'materials_used'
    ]
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, 'Portfolio item created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('core:portfolio_list', kwargs={'user_id': self.request.user.id})


class PortfolioUpdateView(LoginRequiredMixin, UpdateView):
    """Update portfolio item"""
    model = PortfolioItem
    template_name = 'core/portfolio/edit.html'
    fields = [
        'title', 'description', 'category', 'image', 'video',
        'project_date', 'location', 'budget', 'duration',
        'client_name', 'client_testimonial',
        'before_image', 'after_image', 'tags', 'materials_used',
        'is_featured', 'is_public', 'sort_order'
    ]
    
    def get_queryset(self):
        return super().get_queryset().filter(provider=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Portfolio item updated successfully!')
        return super().form_valid(form)


@login_required
@require_POST
def portfolio_delete(request, item_id):
    """Delete portfolio item"""
    item = get_object_or_404(PortfolioItem, id=item_id, provider=request.user)
    item.delete()
    messages.success(request, 'Portfolio item deleted successfully!')
    return redirect('core:portfolio_list', user_id=request.user.id)


# Review Views
class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Create new review"""
    model = EnhancedReview
    template_name = 'core/reviews/create.html'
    fields = [
        'overall_rating', 'work_quality', 'communication',
        'timeliness', 'value_for_money', 'title', 'comment',
        'pros', 'cons'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user can review this provider"""
        self.provider = get_object_or_404(User, id=kwargs['provider_id'], user_type='service_provider')
        
        # Check if user has already reviewed this provider
        if EnhancedReview.objects.filter(
            homeowner=request.user,
            service_provider=self.provider
        ).exists():
            messages.error(request, 'You have already reviewed this provider.')
            return redirect('users:profile', pk=self.provider.id)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.homeowner = self.request.user
        form.instance.service_provider = self.provider
        
        # Try to get related gig/order from URL parameters
        gig_id = self.request.GET.get('gig')
        order_id = self.request.GET.get('order')
        
        if gig_id:
            form.instance.gig = get_object_or_404(Gig, id=gig_id)
        elif order_id:
            form.instance.order = get_object_or_404(Order, id=order_id)
        
        messages.success(self.request, 'Review submitted successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provider'] = self.provider
        return context
    
    def get_success_url(self):
        return reverse_lazy('users:profile', kwargs={'pk': self.provider.id})


@login_required
@require_POST
def review_helpful(request, review_id):
    """Vote on review helpfulness"""
    review = get_object_or_404(EnhancedReview, id=review_id)
    helpful = request.POST.get('helpful') == 'true'
    
    review.mark_as_helpful(helpful)
    
    return JsonResponse({
        'helpful_votes': review.helpful_votes,
        'total_votes': review.total_votes,
        'helpfulness_percentage': review.helpfulness_percentage
    })


# Availability Calendar Views
@login_required
def availability_calendar(request, user_id=None):
    """View availability calendar"""
    if user_id:
        provider = get_object_or_404(User, id=user_id, user_type='service_provider')
    else:
        provider = request.user
    
    # Get or create calendar
    calendar, created = AvailabilityCalendar.objects.get_or_create(provider=provider)
    
    # Get availability slots for current month
    from datetime import datetime, timedelta
    today = timezone.now().date()
    start_date = today.replace(day=1)
    
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)
    
    end_date = end_date - timedelta(days=1)
    
    slots = AvailabilitySlot.objects.filter(
        calendar=calendar,
        date__range=[start_date, end_date]
    ).order_by('date', 'start_time')
    
    # Organize slots by date
    slots_by_date = {}
    for slot in slots:
        date_str = slot.date.strftime('%Y-%m-%d')
        if date_str not in slots_by_date:
            slots_by_date[date_str] = []
        slots_by_date[date_str].append(slot)
    
    context = {
        'provider': provider,
        'calendar': calendar,
        'slots_by_date': slots_by_date,
        'current_date': today,
        'is_own_calendar': request.user == provider,
    }
    
    return render(request, 'core/availability/calendar.html', context)


@login_required
@require_POST
def availability_slot_create(request):
    """Create availability slot"""
    calendar = get_object_or_404(AvailabilityCalendar, provider=request.user)
    
    # Parse slot data
    date = request.POST.get('date')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    
    # Create slot
    slot = AvailabilitySlot.objects.create(
        calendar=calendar,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status='available'
    )
    
    return JsonResponse({
        'success': True,
        'slot_id': slot.id,
        'message': 'Availability slot created successfully!'
    })


@login_required
@require_POST
def availability_slot_update(request, slot_id):
    """Update availability slot"""
    slot = get_object_or_404(AvailabilitySlot, id=slot_id, calendar__provider=request.user)
    
    status = request.POST.get('status')
    if status in dict(AvailabilitySlot.STATUS_CHOICES):
        slot.status = status
        slot.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Availability slot updated successfully!'
    })


# Invoice Views
class InvoiceListView(LoginRequiredMixin, ListView):
    """List invoices"""
    model = Invoice
    template_name = 'core/invoices/list.html'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Invoice.objects.filter(
            provider=self.request.user
        ).select_related('homeowner', 'order', 'gig').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    """Create new invoice"""
    model = Invoice
    template_name = 'core/invoices/create.html'
    fields = [
        'homeowner', 'order', 'gig', 'issue_date', 'due_date',
        'subtotal', 'vat_rate', 'notes', 'payment_terms'
    ]
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        messages.success(self.request, 'Invoice created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['homeowners'] = User.objects.filter(
            user_type='homeowner',
            orders__gig__user=self.request.user
        ).distinct()
        return context


@login_required
def invoice_detail(request, invoice_id):
    """View invoice details"""
    invoice = get_object_or_404(
        Invoice, 
        id=invoice_id, 
        provider=request.user
    )
    
    items = invoice.items.all().order_by('sort_order')
    
    context = {
        'invoice': invoice,
        'items': items,
    }
    
    return render(request, 'core/invoices/detail.html', context)


@login_required
@require_POST
def invoice_generate_pdf(request, invoice_id):
    """Generate PDF for invoice"""
    invoice = get_object_or_404(
        Invoice, 
        id=invoice_id, 
        provider=request.user
    )
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from io import BytesIO
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph(f"Invoice {invoice.invoice_number}", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Provider info
        provider_info = [
            [Paragraph("Provider:", styles['Normal']), Paragraph(invoice.provider.get_full_name() or invoice.provider.email, styles['Normal'])],
            [Paragraph("Email:", styles['Normal']), Paragraph(invoice.provider.email, styles['Normal'])],
            [Paragraph("Phone:", styles['Normal']), Paragraph(getattr(invoice.provider.provider_profile, 'phone', 'N/A'), styles['Normal'])],
        ]
        
        provider_table = Table(provider_info)
        story.append(provider_table)
        story.append(Spacer(1, 12))
        
        # Homeowner info
        homeowner_info = [
            [Paragraph("Bill To:", styles['Normal']), Paragraph(invoice.homeowner.get_full_name() or invoice.homeowner.email, styles['Normal'])],
            [Paragraph("Email:", styles['Normal']), Paragraph(invoice.homeowner.email, styles['Normal'])],
        ]
        
        homeowner_table = Table(homeowner_info)
        story.append(homeowner_table)
        story.append(Spacer(1, 12))
        
        # Invoice details
        details_info = [
            [Paragraph("Invoice Date:", styles['Normal']), Paragraph(str(invoice.issue_date), styles['Normal'])],
            [Paragraph("Due Date:", styles['Normal']), Paragraph(str(invoice.due_date), styles['Normal'])],
            [Paragraph("Status:", styles['Normal']), Paragraph(invoice.get_status_display(), styles['Normal'])],
        ]
        
        details_table = Table(details_info)
        story.append(details_table)
        story.append(Spacer(1, 12))
        
        # Items
        items_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
        for item in invoice.items.all():
            items_data.append([
                item.description,
                str(item.quantity),
                f"R{item.unit_price}",
                f"R{item.total_price}"
            ])
        
        items_table = Table(items_data)
        story.append(items_table)
        story.append(Spacer(1, 12))
        
        # Totals
        totals_data = [
            ['Subtotal:', '', '', f"R{invoice.subtotal}"],
            ['VAT:', '', '', f"R{invoice.vat_amount}"],
            ['Total:', '', '', f"R{invoice.total_amount}"],
        ]
        
        totals_table = Table(totals_data)
        story.append(totals_table)
        
        # Build PDF
        doc.build(story)
        
        # Save PDF
        buffer.seek(0)
        filename = f"invoice_{invoice.invoice_number}.pdf"
        
        # Save to model
        from django.core.files.base import ContentFile
        invoice.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
        
        messages.success(request, 'PDF generated successfully!')
        
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
    
    return redirect('core:invoice_detail', invoice_id=invoice_id)


# Dispute Views
class DisputeListView(LoginRequiredMixin, ListView):
    """List disputes"""
    model = Dispute
    template_name = 'core/disputes/list.html'
    paginate_by = 20
    
    def get_queryset(self):
        # Show disputes where user is either initiator or respondent
        queryset = Dispute.objects.filter(
            Q(initiator=self.request.user) | Q(respondent=self.request.user)
        ).select_related('initiator', 'respondent', 'order', 'gig').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


class DisputeCreateView(LoginRequiredMixin, CreateView):
    """Create new dispute"""
    model = Dispute
    template_name = 'core/disputes/create.html'
    fields = [
        'respondent', 'order', 'gig', 'title', 'description',
        'category', 'priority'
    ]
    
    def form_valid(self, form):
        form.instance.initiator = self.request.user
        messages.success(self.request, 'Dispute created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get potential respondents (providers the user has worked with)
        completed_orders = Order.objects.filter(
            homeowner=self.request.user,
            status='completed'
        ).select_related('gig__user')
        
        providers = User.objects.filter(
            id__in=completed_orders.values_list('gig__user', flat=True)
        )
        
        context['providers'] = providers
        context['orders'] = completed_orders
        return context


@login_required
def dispute_detail(request, dispute_id):
    """View dispute details"""
    dispute = get_object_or_404(
        Dispute, 
        id=dispute_id
    )
    
    # Check if user is involved in dispute
    if request.user not in [dispute.initiator, dispute.respondent]:
        messages.error(request, 'You are not authorized to view this dispute.')
        return redirect('core:dispute_list')
    
    messages = DisputeMessage.objects.filter(
        dispute=dispute
    ).select_related('sender').order_by('created_at')
    
    context = {
        'dispute': dispute,
        'messages': messages,
        'is_initiator': request.user == dispute.initiator,
    }
    
    return render(request, 'core/disputes/detail.html', context)


@login_required
@require_POST
def dispute_message_create(request, dispute_id):
    """Add message to dispute"""
    dispute = get_object_or_404(Dispute, id=dispute_id)
    
    # Check if user is involved in dispute
    if request.user not in [dispute.initiator, dispute.respondent]:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    message = request.POST.get('message')
    if message:
        DisputeMessage.objects.create(
            dispute=dispute,
            sender=request.user,
            message=message
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Message sent successfully!'
        })
    
    return JsonResponse({'error': 'Message cannot be empty'}, status=400)


# Analytics Dashboard
@login_required
def analytics_dashboard(request):
    """User analytics dashboard"""
    # Get or create user analytics
    analytics, created = UserAnalytics.objects.get_or_create(user=request.user)
    
    # Update stats
    analytics.update_stats()
    
    # Get recent activity
    recent_reviews = EnhancedReview.objects.filter(
        service_provider=request.user
    ).order_by('-created_at')[:5]
    
    recent_orders = Order.objects.filter(
        gig__user=request.user
    ).order_by('-created_at')[:5]
    
    # Performance metrics
    if request.user.user_type == 'service_provider':
        # Provider metrics
        completion_rate = 0
        if analytics.total_orders_received > 0:
            completion_rate = (analytics.completed_orders / analytics.total_orders_received) * 100
        
        metrics = {
            'completion_rate': completion_rate,
            'average_rating': analytics.average_rating,
            'total_earnings': analytics.total_earnings,
            'active_gigs': analytics.active_gigs,
        }
    else:
        # Homeowner metrics
        metrics = {
            'total_orders': Order.objects.filter(homeowner=request.user).count(),
            'total_spent': Order.objects.filter(
                homeowner=request.user,
                status='completed'
            ).aggregate(total=models.Sum('total_amount'))['total'] or 0,
        }
    
    context = {
        'analytics': analytics,
        'metrics': metrics,
        'recent_reviews': recent_reviews,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'core/analytics/dashboard.html', context)
