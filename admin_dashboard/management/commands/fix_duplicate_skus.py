from django.core.management.base import BaseCommand
from django.utils.text import slugify
from customer_web.models import ProductInventory
from django.db import transaction

class Command(BaseCommand):
    help = 'Fix duplicate SKUs in ProductInventory'

    def handle(self, *args, **options):
        self.stdout.write('Starting SKU duplication fix...')
        
        # Get all inventories
        inventories = ProductInventory.objects.all().order_by('id')
        fixed_count = 0
        
        with transaction.atomic():
            for inventory in inventories:
                # Check if SKU already exists (excluding current record)
                duplicate_sku = ProductInventory.objects.filter(
                    sku=inventory.sku
                ).exclude(id=inventory.id).exists()
                
                if duplicate_sku or not inventory.sku:
                    # Generate new unique SKU
                    base_sku = f"{slugify(inventory.product.name)}-{slugify(inventory.color)}-{inventory.size}"
                    new_sku = base_sku
                    counter = 1
                    
                    # Ensure new SKU is unique
                    while ProductInventory.objects.filter(sku=new_sku).exists():
                        new_sku = f"{base_sku}-{counter}"
                        counter += 1
                    
                    old_sku = inventory.sku
                    inventory.sku = new_sku
                    inventory.save()
                    fixed_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Fixed SKU: {old_sku} -> {new_sku} for {inventory.product.name} ({inventory.size}, {inventory.color})'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_count} duplicate SKUs')
        )
