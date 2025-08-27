from customer_web.models import Category

print('Categories matching navigation:')
test_slugs = ['do-bo-be-gai', 'ao-be-gai', 'quan-be-trai', 'giay-dep-be-gai']

for slug in test_slugs:
    cat = Category.objects.filter(slug=slug).first()
    print(f'{slug}: {cat.name if cat else "Not found"}')

print(f'\nTotal categories: {Category.objects.count()}')
