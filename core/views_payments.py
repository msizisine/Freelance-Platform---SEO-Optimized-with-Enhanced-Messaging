"""
Views for provider payment processing and management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta

from .models import User
from .models_payments import ProviderEarnings, ProviderPayout, MonthlyServiceFee, PaymentTransaction

# Lazy import to prevent ModuleNotFoundError when Django settings aren't configured
try:
    from .services.payment_service import PaymentProcessingService
except ImportError:
    PaymentProcessingService = None


def is_service_provider(user):
    """Check if user is a service provider"""
    return user.is_authenticated and user.user_type == 'service_provider'


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_superuser
