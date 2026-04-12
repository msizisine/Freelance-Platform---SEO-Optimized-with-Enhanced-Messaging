from django.core.management.base import BaseCommand
from gigs.models import Category, Subcategory


class Command(BaseCommand):
    help = 'Create default categories and subcategories for the gig platform'

    def handle(self, *args, **options):
        # Default categories and their subcategories
        default_data = {
            'Electrical': [
                'Residential Wiring',
                'Commercial Wiring',
                'Industrial Electrical',
                'Lighting Installation',
                'Electrical Repairs',
                'Panel Installation',
                'Generator Installation',
                'Security Systems',
                'Home Automation',
                'Electrical Inspection'
            ],
            'Plumbing': [
                'Residential Plumbing',
                'Commercial Plumbing',
                'Pipe Installation',
                'Drain Cleaning',
                'Water Heater Installation',
                'Bathroom Plumbing',
                'Kitchen Plumbing',
                'Sewer Line Repair',
                'Gas Line Installation',
                'Plumbing Inspection'
            ],
            'Construction': [
                'Home Building',
                'Commercial Construction',
                'Renovation',
                'Remodeling',
                'Foundation Work',
                'Roofing',
                'Framing',
                'Drywall Installation',
                'Painting',
                'Flooring Installation'
            ],
            'HVAC': [
                'Air Conditioning',
                'Heating Systems',
                'Ventilation',
                'HVAC Installation',
                'HVAC Repair',
                'Duct Work',
                'Thermostat Installation',
                'Indoor Air Quality',
                'Energy Efficiency',
                'HVAC Maintenance'
            ],
            'Landscaping': [
                'Lawn Care',
                'Garden Design',
                'Tree Services',
                'Irrigation Systems',
                'Hardscaping',
                'Outdoor Lighting',
                'Landscape Maintenance',
                'Sod Installation',
                'Fence Installation',
                'Patio Construction'
            ],
            'Cleaning': [
                'House Cleaning',
                'Office Cleaning',
                'Deep Cleaning',
                'Carpet Cleaning',
                'Window Cleaning',
                'Pressure Washing',
                'Post-Construction Cleaning',
                'Move-in/Move-out Cleaning',
                'Janitorial Services',
                'Disinfection Services'
            ],
            'Automotive': [
                'Car Repair',
                'Oil Change',
                'Brake Service',
                'Engine Repair',
                'Transmission Service',
                'Auto Detailing',
                'Tire Service',
                'Battery Service',
                'AC Service',
                'Diagnostic Services'
            ],
            'Technology': [
                'Computer Repair',
                'Network Setup',
                'Web Development',
                'Mobile App Development',
                'IT Support',
                'Data Recovery',
                'Cybersecurity',
                'Cloud Services',
                'Software Installation',
                'Hardware Installation'
            ],
            'Appliance Repair': [
                'Refrigerator Repair',
                'Washer/Dryer Repair',
                'Dishwasher Repair',
                'Oven/Stove Repair',
                'Microwave Repair',
                'Small Appliance Repair',
                'Garage Door Repair',
                'HVAC Appliance Service',
                'Installation Services',
                'Maintenance Services'
            ],
            'Painting': [
                'Interior Painting',
                'Exterior Painting',
                'Commercial Painting',
                'Residential Painting',
                'Wallpaper Installation',
                'Pressure Washing',
                'Staining',
                'Texture Application',
                'Color Consultation',
                'Surface Preparation'
            ]
        }

        created_categories = 0
        created_subcategories = 0

        for category_name, subcategory_names in default_data.items():
            # Create or get category
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': f'Professional {category_name.lower()} services',
                    'icon': self.get_icon_for_category(category_name)
                }
            )
            
            if created:
                created_categories += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category_name}'))
            
            # Create subcategories
            for subcategory_name in subcategory_names:
                subcategory, created = Subcategory.objects.get_or_create(
                    category=category,
                    name=subcategory_name
                )
                
                if created:
                    created_subcategories += 1
                    self.stdout.write(self.style.SUCCESS(f'  Created subcategory: {subcategory_name}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_categories} categories and {created_subcategories} subcategories'
            )
        )

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
            'Painting': 'fas fa-paint-brush'
        }
        return icons.get(category_name, 'fas fa-tools')
