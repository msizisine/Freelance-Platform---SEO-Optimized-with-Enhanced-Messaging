from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from django.urls import reverse
from django.db import transaction
from gigs.models import Gig, JobApplication
from reviews.models import Review
from orders.models import Order
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from decimal import Decimal
from datetime import datetime

@login_required
def complete_job_with_invoice(request, pk):
    """Complete job with invoice generation and payment release"""
    gig = get_object_or_404(Gig, pk=pk)
    
    # Check if user owns the job
    if gig.homeowner != request.user:
        messages.error(request, 'You can only complete your own jobs.')
        return redirect('gigs:detail', pk=pk)
    
    # Check if job is in active status
    if gig.job_status != 'active':
        messages.error(request, 'Only active jobs can be marked as complete.')
        return redirect('gigs:detail', pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Update job status to completed
            gig.job_status = 'completed'
            gig.save()
            
            # Create order record for payment processing
            order = Order.objects.create(
                gig=gig,
                homeowner=gig.homeowner,
                service_provider=gig.hired_provider,
                status='completed',
                total_amount=gig.budget_max or gig.budget_min,  # Use max budget as total
                created_at=datetime.now()
            )
            
            # Generate invoice
            invoice_data = generate_invoice(gig, gig.hired_provider, order)
            
            # Redirect to review creation with invoice context
            messages.success(request, 'Job marked as complete. Please rate the service provider.')
            return redirect('reviews:create_review_with_invoice', 
                      user_id=gig.hired_provider.pk, 
                      order_id=order.pk,
                      job_id=gig.pk)
    
    # Show confirmation page
    context = {
        'gig': gig,
        'service_provider': gig.hired_provider,
        'proposed_amount': gig.budget_max or gig.budget_min
    }
    return render(request, 'gigs/complete_job_with_invoice.html', context)

def get_invoice_data(gig, service_provider, order):
    """Get invoice data as dictionary for template display"""
    
    invoice_data = {
        'invoice_number': str(order.pk)[:8].upper(),  # Short version for display
        'date_issued': datetime.now(),
        'service_provider_name': f"{service_provider.first_name} {service_provider.last_name}" if service_provider.first_name else service_provider.email,
        'service_provider_email': service_provider.email,
        'client_name': f"{order.homeowner.first_name} {order.homeowner.last_name}" if order.homeowner.first_name else order.homeowner.email,
        'client_email': order.homeowner.email,
        'service_title': gig.title,
        'service_description': gig.description[:100] + '...' if len(gig.description) > 100 else gig.description,
        'location': gig.location,
        'base_price': float(order.total_amount),
        'additional_fees': 0.00,
        'discount_amount': 0.00,
        'total_amount': float(order.total_amount),
        'order_number': order.order_number,
        'completed_date': datetime.now().strftime('%B %d, %Y'),
    }
    
    return invoice_data

@login_required
def download_invoice(request, order_id):
    """Download PDF invoice for an order"""
    order = get_object_or_404(Order, pk=order_id)
    
    # Check if user can access this invoice
    if request.user not in [order.homeowner, order.service_provider]:
        messages.error(request, 'You do not have permission to access this invoice.')
        return redirect('orders:detail', pk=order.pk)
    
    # Generate PDF
    pdf_data = generate_invoice(order.gig, order.service_provider, order)
    
    # Create response
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_number}.pdf"'
    response['Content-Length'] = len(pdf_data)
    
    return response

def generate_invoice(gig, service_provider, order):
    """Generate PDF invoice for completed job"""
    
    # Create PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create content
    elements = []
    
    # Header
    elements.append(Paragraph("INVOICE", styles['Title']))
    elements.append(Paragraph(f"Invoice #{order.pk}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    
    # Job Information
    elements.append(Paragraph("Job Details", styles['Heading2']))
    
    job_data = [
        ['Job Title:', gig.title],
        ['Description:', gig.description[:100] + '...' if len(gig.description) > 100 else gig.description],
        ['Location:', gig.location],
        ['Budget:', f"R{gig.budget_min} - R{gig.budget_max}"],
        ['Completed Date:', datetime.now().strftime('%B %d, %Y')],
    ]
    
    job_table = Table(job_data, colWidths=[2*inch, 4*inch])
    job_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(job_table)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # Service Provider Information
    elements.append(Paragraph("Service Provider", styles['Heading2']))
    
    provider_data = [
        ['Name:', f"{service_provider.first_name} {service_provider.last_name}"],
        ['Email:', service_provider.email],
        ['Phone:', getattr(service_provider, 'phone', 'N/A')],
        ['Payment Amount:', f"R{order.total_amount}"],
    ]
    
    provider_table = Table(provider_data, colWidths=[2*inch, 4*inch])
    provider_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(provider_table)
    
    # Payment Information
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    elements.append(Paragraph("Payment Information", styles['Heading2']))
    
    payment_data = [
        ['Total Amount:', f"R{order.total_amount}"],
        ['Status:', 'Paid from Escrow'],
        ['Payment Date:', datetime.now().strftime('%B %d, %Y')],
        ['Method:', 'Direct Transfer'],
    ]
    
    payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(payment_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF value
    pdf_value = buffer.getvalue()
    buffer.close()
    
    return pdf_value
