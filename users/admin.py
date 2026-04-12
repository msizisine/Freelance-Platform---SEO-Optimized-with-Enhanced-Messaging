from django.contrib import admin
from .models import Profile, Portfolio, Education, WorkExperience, Certification


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'hourly_rate', 'availability_status', 'verification_status')
    list_filter = ('availability_status', 'verification_status', 'gender')
    search_fields = ('user__email', 'phone_number')


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'title')


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'degree', 'start_date', 'is_current')
    list_filter = ('is_current', 'start_date')
    search_fields = ('user__email', 'institution', 'degree')


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'position', 'start_date', 'is_current')
    list_filter = ('is_current', 'start_date')
    search_fields = ('user__email', 'company', 'position')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'issuing_organization', 'issue_date', 'expiry_date')
    list_filter = ('issue_date', 'expiry_date')
    search_fields = ('user__email', 'name', 'issuing_organization')
