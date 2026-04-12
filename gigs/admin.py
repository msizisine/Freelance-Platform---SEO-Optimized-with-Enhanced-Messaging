from django.contrib import admin
from .models import Category, Subcategory, Gig, GigPackage, GigRequirement, GigFAQ, GigGallery


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    # prepopulated_fields = {'slug': ('name',')}  # Removed since slug field doesn't exist


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')


class GigPackageInline(admin.TabularInline):
    model = GigPackage
    extra = 0


class GigRequirementInline(admin.TabularInline):
    model = GigRequirement
    extra = 1


class GigFAQInline(admin.TabularInline):
    model = GigFAQ
    extra = 1


class GigGalleryInline(admin.TabularInline):
    model = GigGallery
    extra = 1


@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):
    list_display = ('title', 'homeowner', 'category', 'location', 'budget_display', 'status', 'is_active', 'created_at')
    list_filter = ('category', 'status', 'is_active', 'is_featured', 'created_at')
    search_fields = ('title', 'homeowner__email', 'description', 'location')
    readonly_fields = ('views', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('homeowner', 'title', 'description', 'category', 'subcategory', 'tags', 'image', 'video')
        }),
        ('Job Details', {
            'fields': ('budget_min', 'budget_max', 'location', 'urgency', 'requires_approval')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_active', 'status')
        }),
        ('Statistics', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def budget_display(self, obj):
        return obj.get_budget_display()
    budget_display.short_description = 'Budget'


@admin.register(GigPackage)
class GigPackageAdmin(admin.ModelAdmin):
    list_display = ('gig', 'name', 'title', 'price', 'delivery_days', 'revisions')
    list_filter = ('name', 'delivery_days')
    search_fields = ('gig__title', 'title', 'description')


@admin.register(GigRequirement)
class GigRequirementAdmin(admin.ModelAdmin):
    list_display = ('gig', 'requirement', 'is_required')
    search_fields = ('gig__title', 'requirement')


@admin.register(GigFAQ)
class GigFAQAdmin(admin.ModelAdmin):
    list_display = ('gig', 'question')
    search_fields = ('gig__title', 'question', 'answer')


@admin.register(GigGallery)
class GigGalleryAdmin(admin.ModelAdmin):
    list_display = ('gig', 'caption')
    search_fields = ('gig__title', 'caption')
