from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from django.conf import settings
import os
from datetime import datetime


def generate_invoice_pdf(order, job_application):
    """
    Generate a PDF invoice for a completed job
    
    Args:
        order: Order instance
        job_application: Accepted JobApplication instance
    
    Returns:
        str: Path to generated PDF file
    """
    # Create invoices directory if it doesn't exist
    invoices_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(invoices_dir, exist_ok=True)
    
    # Generate filename
    filename = f"invoice_{order.order_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(invoices_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    # Title
    story.append(Paragraph("INVOICE", title_style))
    story.append(Spacer(1, 20))
    
    # Invoice header information
    invoice_data = [
        ["Invoice Number:", order.order_number],
        ["Date:", datetime.now().strftime("%B %d, %Y")],
        ["Status:", order.get_status_display().title()],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(invoice_table)
    story.append(Spacer(1, 30))
    
    # Service Provider Information (From)
    story.append(Paragraph("FROM:", heading_style))
    provider_info = [
        [job_application.service_provider.get_full_name() or job_application.service_provider.email],
        [job_application.service_provider.email],
        [job_application.service_provider.phone if hasattr(job_application.service_provider, 'phone') else ''],
        ["Service Provider"]
    ]
    
    provider_table = Table(provider_info, colWidths=[6*inch])
    provider_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(provider_table)
    story.append(Spacer(1, 20))
    
    # Homeowner Information (Bill To)
    story.append(Paragraph("BILL TO:", heading_style))
    homeowner_info = [
        [order.homeowner.get_full_name() or order.homeowner.email],
        [order.homeowner.email],
        [order.homeowner.phone if hasattr(order.homeowner, 'phone') else ''],
        ["Homeowner"]
    ]
    
    homeowner_table = Table(homeowner_info, colWidths=[6*inch])
    homeowner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(homeowner_table)
    story.append(Spacer(1, 30))
    
    # Job Details
    story.append(Paragraph("JOB DETAILS:", heading_style))
    
    job_data = [
        ["Job Title:", order.gig.title],
        ["Description:", order.gig.description[:200] + "..." if len(order.gig.description) > 200 else order.gig.description],
        ["Proposed Rate:", f"R{job_application.proposed_rate}"],
        ["Estimated Duration:", job_application.estimated_duration or "Not specified"],
        ["Application Date:", job_application.applied_at.strftime("%B %d, %Y") if job_application.applied_at else "Not specified"],
    ]
    
    job_table = Table(job_data, colWidths=[2*inch, 4*inch])
    job_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(job_table)
    story.append(Spacer(1, 30))
    
    # Amount Due
    story.append(Paragraph("PAYMENT DETAILS:", heading_style))
    
    amount_data = [
        ["Subtotal:", f"R{job_application.proposed_rate}"],
        ["Tax (0%):", "R0.00"],
        ["Total Amount Due:", f"R{job_application.proposed_rate}"],
    ]
    
    amount_table = Table(amount_data, colWidths=[4*inch, 2*inch])
    amount_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -2), 'LEFT'),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 11),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(amount_table)
    story.append(Spacer(1, 40))
    
    # Footer notes
    notes_style = ParagraphStyle(
        'Notes',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    story.append(Paragraph("Thank you for your business!", notes_style))
    story.append(Paragraph(f"This invoice was generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", notes_style))
    
    # Build PDF
    doc.build(story)
    
    return filepath
