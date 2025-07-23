from django.core.management.base import BaseCommand
from customer_web.models import Category, Product
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Create sample data for Korean fashion store'

    def handle(self, *args, **options):
        # Create categories
        categories_data = [
            {
                'name': 'Áo khoác',
                'description': 'Áo khoác thời trang Hàn Quốc, phong cách hiện đại',
            },
            {
                'name': 'Áo thun',
                'description': 'Áo thun basic và trendy từ Hàn Quốc',
            },
            {
                'name': 'Quần',
                'description': 'Quần dài, quần short phong cách Hàn Quốc',
            },
            {
                'name': 'Váy',
                'description': 'Váy xinh xắn, dễ thương theo phong cách Hàn',
            },
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'description': cat_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create products
        products_data = [
            {
                'name': 'Áo khoác denim oversized',
                'category': 'Áo khoác',
                'description': 'Áo khoác denim phong cách oversized trendy, chất liệu bền đẹp',
                'price': 450000,
                'discount_price': 350000,
                'stock': 20,
                'sizes': 'S,M,L,XL',
                'colors': 'blue,black,white',
                'is_featured': True,
            },
            {
                'name': 'Áo thun basic cotton',
                'category': 'Áo thun',
                'description': 'Áo thun basic 100% cotton, form chuẩn Hàn Quốc',
                'price': 180000,
                'stock': 50,
                'sizes': 'XS,S,M,L',
                'colors': 'white,black,gray,pink',
                'is_featured': True,
            },
            {
                'name': 'Quần jeans skinny',
                'category': 'Quần',
                'description': 'Quần jeans skinny co giãn, form đẹp ôm dáng',
                'price': 380000,
                'discount_price': 299000,
                'stock': 30,
                'sizes': 'S,M,L,XL',
                'colors': 'blue,black',
                'is_featured': False,
            },
            {
                'name': 'Váy midi hoa nhí',
                'category': 'Váy',
                'description': 'Váy midi họa tiết hoa nhí xinh xắn, phong cách vintage Hàn',
                'price': 320000,
                'stock': 25,
                'sizes': 'S,M,L',
                'colors': 'pink,white,beige',
                'is_featured': True,
            },
            {
                'name': 'Áo hoodie unisex',
                'category': 'Áo khoác',
                'description': 'Áo hoodie unisex form rộng, chất nỉ mềm mại',
                'price': 420000,
                'stock': 40,
                'sizes': 'S,M,L,XL,XXL',
                'colors': 'gray,black,navy,beige',
                'is_featured': False,
            },
            {
                'name': 'Áo thun crop top',
                'category': 'Áo thun',
                'description': 'Áo thun crop top trendy, phù hợp mix đồ',
                'price': 150000,
                'stock': 35,
                'sizes': 'XS,S,M,L',
                'colors': 'white,black,pink,yellow',
                'is_featured': False,
            }
        ]

        for prod_data in products_data:
            try:
                category = Category.objects.get(name=prod_data['category'])
                product, created = Product.objects.get_or_create(
                    name=prod_data['name'],
                    defaults={
                        'slug': slugify(prod_data['name']),
                        'category': category,
                        'description': prod_data['description'],
                        'price': prod_data['price'],
                        'discount_price': prod_data.get('discount_price'),
                        'stock': prod_data['stock'],
                        'sizes': prod_data['sizes'],
                        'colors': prod_data['colors'],
                        'is_featured': prod_data['is_featured'],
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created product: {product.name}')
                
            except Category.DoesNotExist:
                self.stdout.write(f'Category {prod_data["category"]} not found')

        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))
