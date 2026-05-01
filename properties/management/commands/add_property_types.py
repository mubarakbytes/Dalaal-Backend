from django.core.management.base import BaseCommand
from properties.models import PropertyCategory, PropertySubtype


class Command(BaseCommand):
    help = 'Add default property categories and subtypes'

    def handle(self, *args, **options):
        # Clear existing data
        PropertySubtype.objects.all().delete()
        PropertyCategory.objects.all().delete()
        
        categories_data = [
            {
                'name': 'House',
                'name_so': 'Guri',
                'icon': 'home',
                'subtypes': ['Villa', 'Duplex', 'Traditional House', 'Townhouse', 'Studio']
            },
            {
                'name': 'Apartment',
                'name_so': 'Apartment',
                'icon': 'apartment',
                'subtypes': ['Studio', '1 Bedroom', '2 Bedrooms', '3+ Bedrooms', 'Penthouse']
            },
            {
                'name': 'Land',
                'name_so': 'Dhul',
                'icon': 'terrain',
                'subtypes': ['Residential', 'Commercial', 'Agricultural', 'Industrial', 'Mixed Use', 'Beachfront']
            },
            {
                'name': 'Warehouse',
                'name_so': 'Bakhaarka',
                'icon': 'warehouse',
                'subtypes': ['Storage', 'Manufacturing', 'Cold Storage', 'Distribution Center', 'Showroom']
            },
            {
                'name': 'Commercial',
                'name_so': 'Ganacsi',
                'icon': 'storefront',
                'subtypes': ['Office', 'Shop', 'Restaurant', 'Hotel', 'Clinic', 'School']
            },
        ]
        
        for cat_data in categories_data:
            category, created = PropertyCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'name_so': cat_data['name_so'],
                    'icon': cat_data['icon']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            
            for subtype_name in cat_data['subtypes']:
                subtype, created = PropertySubtype.objects.get_or_create(
                    category=category,
                    name=subtype_name
                )
                if created:
                    self.stdout.write(f'  Created subtype: {subtype.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully added property categories and subtypes!'))
