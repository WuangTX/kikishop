from django.core.management.base import BaseCommand
from customer_web.models import Product, ProductInventory
import random

class Command(BaseCommand):
    help = 'Create sample inventory data for products'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample inventory data...')
        
        # Get all products
        products = Product.objects.all()
        
        if not products.exists():
            self.stdout.write(self.style.ERROR('No products found. Please create some products first.'))
            return
        
        # Clear existing inventory
        ProductInventory.objects.all().delete()
        
        # Sample sizes and colors that match model choices
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        colors = ['white', 'black', 'gray', 'beige', 'pink', 'blue', 'navy', 'brown']
        
        total_created = 0
        
        for product in products:
            # Get available sizes and colors from product
            product_sizes = [size.strip() for size in product.sizes.split(',') if size.strip()] if product.sizes else sizes[:4]
            product_colors = [color.strip() for color in product.colors.split(',') if color.strip()] if product.colors else colors[:3]
            
            # Create inventory for each size-color combination
            for size in product_sizes:
                for color in product_colors:
                    # Random quantity between 0 and 50
                    quantity = random.randint(0, 50)
                    
                    try:
                        inventory, created = ProductInventory.objects.get_or_create(
                            product=product,
                            size=size,
                            color=color,
                            defaults={'quantity': quantity}
                        )
                        
                        if created:
                            total_created += 1
                            self.stdout.write(f'Created inventory: {product.name} - {size} - {color} ({quantity})')
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Error creating inventory for {product.name} - {size} - {color}: {str(e)}')
                        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {total_created} inventory records.')
        )
