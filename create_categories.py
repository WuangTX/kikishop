from customer_web.models import Category

# Tạo các subcategories cho Quần áo bé gái
categories_be_gai = [
    ('do-bo-be-gai', 'Đồ bộ bé gái'),
    ('vay-dam-be-gai', 'Váy đầm bé gái'),
    ('ao-be-gai', 'Áo bé gái'),
    ('quan-be-gai', 'Quần bé gái'),
    ('do-boi-be-gai', 'Đồ bơi bé gái'),
]

# Tạo các subcategories cho Quần áo bé trai
categories_be_trai = [
    ('do-bo-be-trai', 'Đồ bộ bé trai'),
    ('ao-be-trai', 'Áo bé trai'),
    ('quan-be-trai', 'Quần bé trai'),
    ('do-boi-be-trai', 'Đồ bơi bé trai'),
]

# Tạo các subcategories cho Phụ kiện
categories_phu_kien = [
    ('giay-dep-be-gai', 'Giày dép bé gái'),
    ('giay-dep-cho-be-trai', 'Giày dép bé trai'),
    ('non-mu-cho-be', 'Nón mũ cho bé'),
    ('ba-lo-tui-deo', 'Ba lô túi đeo'),
]

# Tạo các subcategories cho Quần áo sơ sinh
categories_so_sinh = [
    ('body-ao-lien-quan', 'Body áo liền quần'),
    ('do-bo-so-sinh', 'Đồ bộ sơ sinh'),
    ('ao-so-sinh', 'Phụ kiện sơ sinh'),
]

# Tạo tất cả categories
all_categories = categories_be_gai + categories_be_trai + categories_phu_kien + categories_so_sinh

for slug, name in all_categories:
    category, created = Category.objects.get_or_create(
        slug=slug,
        defaults={
            'name': name,
            'is_active': True
        }
    )
    if created:
        print(f"Created: {name} -> {slug}")
    else:
        print(f"Exists: {name} -> {slug}")

print(f"\nTotal categories now: {Category.objects.count()}")
