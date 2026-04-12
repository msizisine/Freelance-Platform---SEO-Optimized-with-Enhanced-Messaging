from django import forms
from .models import Category, Subcategory


class CategoryForm(forms.ModelForm):
    """Form for creating and updating categories"""
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name (e.g., Electrical, Plumbing)',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description',
                'required': False
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter FontAwesome icon class (e.g., fas fa-bolt)',
                'required': False
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Category Name'
        self.fields['description'].label = 'Description'
        self.fields['icon'].label = 'Icon Class'

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip().title()
            # Check for duplicate names (case-insensitive)
            existing = Category.objects.filter(name__iexact=name)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(f'Category "{name}" already exists.')
        return name

    def clean_icon(self):
        icon = self.cleaned_data.get('icon')
        if icon:
            icon = icon.strip()
            # Basic validation for FontAwesome icon format
            if not icon.startswith('fa'):
                raise forms.ValidationError('Icon should start with "fa" (e.g., "fas fa-bolt")')
        return icon


class SubcategoryForm(forms.ModelForm):
    """Form for creating and updating subcategories"""
    class Meta:
        model = Subcategory
        fields = ['category', 'name']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subcategory name (e.g., Residential Wiring)',
                'required': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].label = 'Parent Category'
        self.fields['name'].label = 'Subcategory Name'
        
        # Order categories by name
        self.fields['category'].queryset = Category.objects.order_by('name')

    def clean_name(self):
        name = self.cleaned_data.get('name')
        category = self.cleaned_data.get('category')
        
        if name and category:
            name = name.strip().title()
            # Check for duplicate subcategories within the same category
            existing = Subcategory.objects.filter(
                category=category,
                name__iexact=name
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(f'Subcategory "{name}" already exists in this category.')
        return name


class BulkCategoryForm(forms.Form):
    """Form for bulk creating categories"""
    categories_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter categories (one per line):\nElectrical\nPlumbing\nConstruction\n\nOr with descriptions:\nElectrical:Electrical services and installations\nPlumbing:Plumbing and pipe fitting services',
            'required': True
        }),
        label='Categories',
        help_text='Enter one category per line. Optional: add description after colon.'
    )

    def clean_categories_text(self):
        text = self.cleaned_data.get('categories_text')
        if not text:
            raise forms.ValidationError('Please enter at least one category.')
        return text.strip()

    def parse_categories(self):
        """Parse the text input into category data"""
        text = self.cleaned_data.get('categories_text', '')
        categories = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if ':' in line:
                parts = line.split(':', 1)
                name = parts[0].strip().title()
                description = parts[1].strip()
            else:
                name = line.strip().title()
                description = ''
            
            if name:
                categories.append({
                    'name': name,
                    'description': description,
                    'icon': self.get_icon_for_category(name)
                })
        
        return categories

    def get_icon_for_category(self, category_name):
        """Return an appropriate icon for each category"""
        icons = {
            'Electrical': 'fas fa-bolt',
            'Plumbing': 'fas fa-wrench',
            'Construction': 'fas fa-hammer',
            'HVAC': 'fas fa-wind',
            'Landscaping': 'fas fa-tree',
            'Cleaning': 'fas fa-broom',
            'Automotive': 'fas fa-car',
            'Technology': 'fas fa-laptop',
            'Appliance Repair': 'fas fa-blender',
            'Painting': 'fas fa-paint-brush',
            'Building': 'fas fa-building',
            'Gardening': 'fas fa-seedling',
            'General Work': 'fas fa-tools'
        }
        return icons.get(category_name, 'fas fa-tools')
