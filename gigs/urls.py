from django.urls import path, include
from .views import (
    GigListView, GigDetailView, GigCreateView, GigUpdateView, GigDeleteView,
    my_gigs, toggle_gig_status, gig_analytics, category_gigs, service_providers,
    accept_job, reject_job, my_jobs, my_provider_jobs, create_quotation_request, quotation_detail,
    respond_to_quotation, select_quotation, reject_quotation, update_quotation, my_quotations, provider_quotations, apply_for_job, job_applications,
    update_application_status, complete_job, update_job_status, view_invoice, leave_review
)
from .views_invoice import download_invoice
from .views_admin import (
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
    SubcategoryListView, SubcategoryCreateView, SubcategoryUpdateView, SubcategoryDeleteView,
    admin_dashboard
)

app_name = 'gigs'

urlpatterns = [
    path('', GigListView.as_view(), name='list'),
    path('create/', GigCreateView.as_view(), name='create'),
    path('my-gigs/', my_gigs, name='my_gigs'),
    path('my-provider-jobs/', my_provider_jobs, name='my_provider_jobs'),
    path('my-jobs/', my_jobs, name='my_jobs'),
    path('my-quotations/', my_quotations, name='my_quotations'),
    path('provider-quotations/', provider_quotations, name='provider_quotations'),
    path('service-providers/', service_providers, name='service_providers'),
    path('request-quotation/', create_quotation_request, name='create_quotation_request'),
    path('quotation/<int:pk>/', quotation_detail, name='quotation_detail'),
    path('quotation/<int:pk>/respond/', respond_to_quotation, name='respond_to_quotation'),
    path('quotation/<int:pk>/select/<int:response_id>/', select_quotation, name='select_quotation'),
    path('quotation/<int:pk>/reject/<int:response_id>/', reject_quotation, name='reject_quotation'),
    path('quotation/<int:pk>/update/', update_quotation, name='update_quotation'),
    path('<int:pk>/', GigDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', GigUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', GigDeleteView.as_view(), name='delete'),
    path('<int:pk>/toggle-status/', toggle_gig_status, name='toggle_status'),
    path('<int:pk>/analytics/', gig_analytics, name='analytics'),
    path('<int:pk>/accept/', accept_job, name='accept_job'),
    path('<int:pk>/reject/', reject_job, name='reject_job'),
    path('<int:pk>/apply/', apply_for_job, name='apply_for_job'),
    path('<int:pk>/applications/', job_applications, name='job_applications'),
    path('<int:pk>/complete/', complete_job, name='complete_job'),
    path('<int:pk>/update-status/', update_job_status, name='update_job_status'),
    path('application/<int:pk>/update/', update_application_status, name='update_application_status'),
    path('category/<str:name>/', category_gigs, name='category'),
    path('invoice/<int:pk>/', view_invoice, name='invoice_detail'),
    path('download-invoice/<uuid:order_id>/', download_invoice, name='download_invoice'),
    path('<int:pk>/review/', leave_review, name='review_job'),
    
    # Admin Category Management URLs
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('admin/categories/', CategoryListView.as_view(), name='admin_category_list'),
    path('admin/categories/create/', CategoryCreateView.as_view(), name='admin_category_create'),
    path('admin/categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='admin_category_update'),
    path('admin/categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='admin_category_delete'),
    path('admin/subcategories/', SubcategoryListView.as_view(), name='admin_subcategory_list'),
    path('admin/subcategories/create/', SubcategoryCreateView.as_view(), name='admin_subcategory_create'),
    path('admin/subcategories/<int:pk>/edit/', SubcategoryUpdateView.as_view(), name='admin_subcategory_update'),
    path('admin/subcategories/<int:pk>/delete/', SubcategoryDeleteView.as_view(), name='admin_subcategory_delete'),
    
    # WhatsApp Quote System URLs
    path('quotes/', include('gigs.urls_quote')),
]
