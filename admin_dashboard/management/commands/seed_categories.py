from django.core.management.base import BaseCommand
from admin_dashboard.models import Category

CATEGORIES = [
    {
        'name': 'Quần áo bé gái',
        'slug': 'quan-ao-be-gai',
        'description': 'Đồ bộ bé gái, Váy đầm bé gái, Áo bé gái, Quần bé gái',
    },
    {
        'name': 'Quần áo bé trai',
        'slug': 'quan-ao-be-trai',
        'description': 'Đồ bộ bé trai, Áo bé trai, Quần bé trai, Đồ bơi bé trai',
    },
    {
        'name': 'Phụ kiện',
        'slug': 'phu-kien',
        'description': 'Giày dép bé gái, Giày dép bé trai, Nón mũ cho bé, Ba lô túi đeo',
    },
    {
        'name': 'Quần áo sơ sinh',
        'slug': 'quan-ao-so-sinh',
        'description': 'Body áo liền quần, Đồ bộ sơ sinh, Phụ kiện sơ sinh',
    },
]

class Command(BaseCommand):
    help = 'Seed default product categories for KiKi Shop'

    def handle(self, *args, **options):
        for cat in CATEGORIES:
            obj, created = Category.objects.get_or_create(
                name=cat['name'],
                defaults={
                    'slug': cat['slug'],
                    'description': cat['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {obj.name}'))
        self.stdout.write(self.style.SUCCESS('Category seeding complete.'))
