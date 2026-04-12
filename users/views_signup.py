from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from gigs.models import Category
from .forms_signup import CustomSignupForm

User = get_user_model()

class CustomSignupView(CreateView):
    form_class = CustomSignupForm
    model = User
    template_name = 'account/signup.html'
    success_url = reverse_lazy('users:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_categories'] = Category.objects.all()
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        try:
            user = form.save()
            
            # Log user in
            from django.contrib.auth import authenticate
            from django.contrib.auth.backends import ModelBackend
            
            # Use the default ModelBackend for login
            backend = ModelBackend()
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            messages.success(self.request, f'Welcome! Your account has been created successfully.')
            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            messages.error(self.request, f'Error creating account: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct errors below.')
        return super().form_invalid(form)
