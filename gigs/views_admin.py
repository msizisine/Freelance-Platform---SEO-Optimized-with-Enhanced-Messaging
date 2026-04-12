from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from .models import Category, Subcategory
from .forms_admin import CategoryForm, SubcategoryForm


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser


class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all categories for superuser management"""
    model = Category
    template_name = 'gigs/admin/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return Category.objects.annotate(
            gig_count=Count('gig'),
            subcategory_count=Count('subcategories')
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_categories'] = Category.objects.count()
        context['total_subcategories'] = Subcategory.objects.count()
        return context


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new category (superuser only)"""
    model = Category
    form_class = CategoryForm
    template_name = 'gigs/admin/category_form.html'
    success_url = reverse_lazy('gigs:admin_category_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Category'
        context['action'] = 'Create'
        return context


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update existing category (superuser only)"""
    model = Category
    form_class = CategoryForm
    template_name = 'gigs/admin/category_form.html'
    success_url = reverse_lazy('gigs:admin_category_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Category'
        context['action'] = 'Update'
        return context


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete category (superuser only)"""
    model = Category
    template_name = 'gigs/admin/category_confirm_delete.html'
    success_url = reverse_lazy('gigs:admin_category_list')

    def test_func(self):
        return self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        gig_count = category.gig_set.count()
        if gig_count > 0:
            messages.error(request, f'Cannot delete category "{category.name}" because it has {gig_count} associated gigs.')
            return redirect('gigs:admin_category_list')
        
        messages.success(request, f'Category "{category.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


class SubcategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all subcategories for superuser management"""
    model = Subcategory
    template_name = 'gigs/admin/subcategory_list.html'
    context_object_name = 'subcategories'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return Subcategory.objects.select_related('category').annotate(
            gig_count=Count('gig')
        ).order_by('category__name', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_subcategories'] = Subcategory.objects.count()
        return context


class SubcategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new subcategory (superuser only)"""
    model = Subcategory
    form_class = SubcategoryForm
    template_name = 'gigs/admin/subcategory_form.html'
    success_url = reverse_lazy('gigs:admin_subcategory_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, f'Subcategory "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Subcategory'
        context['action'] = 'Create'
        return context


class SubcategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update existing subcategory (superuser only)"""
    model = Subcategory
    form_class = SubcategoryForm
    template_name = 'gigs/admin/subcategory_form.html'
    success_url = reverse_lazy('gigs:admin_subcategory_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, f'Subcategory "{form.instance.name}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Subcategory'
        context['action'] = 'Update'
        return context


class SubcategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete subcategory (superuser only)"""
    model = Subcategory
    template_name = 'gigs/admin/subcategory_confirm_delete.html'
    success_url = reverse_lazy('gigs:admin_subcategory_list')

    def test_func(self):
        return self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        subcategory = self.get_object()
        gig_count = subcategory.gig_set.count()
        if gig_count > 0:
            messages.error(request, f'Cannot delete subcategory "{subcategory.name}" because it has {gig_count} associated gigs.')
            return redirect('gigs:admin_subcategory_list')
        
        messages.success(request, f'Subcategory "{subcategory.name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Admin dashboard for category management"""
    context = {
        'total_categories': Category.objects.count(),
        'total_subcategories': Subcategory.objects.count(),
        'categories_with_gigs': Category.objects.annotate(gig_count=Count('gig')).filter(gig_count__gt=0).count(),
        'recent_categories': Category.objects.order_by('-created_at')[:5],
        'popular_categories': Category.objects.annotate(gig_count=Count('gig')).order_by('-gig_count')[:5],
    }
    return render(request, 'gigs/admin/admin_dashboard.html', context)
