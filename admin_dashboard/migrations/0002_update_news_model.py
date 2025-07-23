# Generated migration file for admin_dashboard

from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


def create_news_categories(apps, schema_editor):
    """Create default news categories"""
    NewsCategory = apps.get_model('admin_dashboard', 'NewsCategory')
    categories = [
        {'name': 'Thời trang', 'description': 'Tin tức về xu hướng thời trang'},
        {'name': 'Style', 'description': 'Bí quyết phối đồ và tạo phong cách'},
        {'name': 'Sự kiện', 'description': 'Các sự kiện và hoạt động của shop'},
        {'name': 'Khuyến mãi', 'description': 'Tin tức về các chương trình khuyến mãi'},
    ]
    
    for cat_data in categories:
        slug = slugify(cat_data['name'])
        NewsCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'slug': slug, 'description': cat_data['description']}
        )


def migrate_existing_news(apps, schema_editor):
    """Migrate existing news to new structure"""
    News = apps.get_model('admin_dashboard', 'News')
    NewsCategory = apps.get_model('admin_dashboard', 'NewsCategory')
    
    # Get default category
    default_category = NewsCategory.objects.first()
    
    # Update existing news records
    for news in News.objects.all():
        if not hasattr(news, 'category') or news.category is None:
            news.category = default_category
        
        # Map old fields to new fields
        if hasattr(news, 'excerpt') and not hasattr(news, 'summary'):
            news.summary = news.excerpt[:500]  # Truncate to 500 chars
        
        if hasattr(news, 'is_published'):
            news.status = 'published' if news.is_published else 'draft'
        
        if hasattr(news, 'is_featured') and news.is_featured:
            news.featured = True
        
        if hasattr(news, 'featured_image') and news.featured_image:
            news.image = news.featured_image
        
        news.save()


class Migration(migrations.Migration):

    dependencies = [
        ('admin_dashboard', '0001_initial'),
    ]

    operations = [
        # Create NewsCategory model
        migrations.CreateModel(
            name='NewsCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Tên danh mục')),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('description', models.TextField(blank=True, verbose_name='Mô tả')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Danh mục tin tức',
                'verbose_name_plural': 'Danh mục tin tức',
                'ordering': ['name'],
            },
        ),
        
        # Rename is_featured to featured
        migrations.RenameField(
            model_name='news',
            old_name='is_featured',
            new_name='featured',
        ),
        
        # Add new fields to News
        migrations.AddField(
            model_name='news',
            name='summary',
            field=models.TextField(default='', max_length=500, verbose_name='Tóm tắt', help_text='Mô tả ngắn về bài viết (tối đa 500 ký tự)'),
            preserve_default=False,
        ),
        
        migrations.AddField(
            model_name='news',
            name='image_position',
            field=models.CharField(choices=[('left', 'Bên trái'), ('right', 'Bên phải'), ('top', 'Phía trên'), ('full', 'Toàn màn hình'), ('center', 'Giữa bài viết')], default='top', max_length=10, verbose_name='Vị trí hình ảnh'),
        ),
        
        migrations.AddField(
            model_name='news',
            name='image_caption',
            field=models.CharField(blank=True, max_length=200, verbose_name='Chú thích hình ảnh'),
        ),
        
        migrations.AddField(
            model_name='news',
            name='external_link',
            field=models.URLField(blank=True, help_text='Link tham khảo hoặc nguồn tin', verbose_name='Liên kết ngoài'),
        ),
        
        migrations.AddField(
            model_name='news',
            name='external_link_text',
            field=models.CharField(blank=True, help_text='Văn bản hiển thị cho liên kết ngoài', max_length=100, verbose_name='Văn bản liên kết'),
        ),
        
        migrations.AddField(
            model_name='news',
            name='tags',
            field=models.CharField(blank=True, help_text='Các thẻ phân cách bằng dấu phẩy', max_length=255, verbose_name='Thẻ'),
        ),
        
        migrations.AddField(
            model_name='news',
            name='status',
            field=models.CharField(choices=[('draft', 'Bản nháp'), ('published', 'Đã xuất bản'), ('archived', 'Lưu trữ')], default='published', max_length=10, verbose_name='Trạng thái'),
        ),
        
        # Create default categories
        migrations.RunPython(create_news_categories),
        
        # Add category field after creating categories
        migrations.AddField(
            model_name='news',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='news', to='admin_dashboard.newscategory', verbose_name='Danh mục'),
        ),
        
        # Rename and modify existing fields
        migrations.RenameField(
            model_name='news',
            old_name='excerpt',
            new_name='old_excerpt',
        ),
        
        migrations.RenameField(
            model_name='news',
            old_name='featured_image',
            new_name='image',
        ),
        
        migrations.RenameField(
            model_name='news',
            old_name='is_published',
            new_name='old_is_published',
        ),
        
        # Change author field from ForeignKey to CharField
        migrations.RemoveField(
            model_name='news',
            name='author',
        ),
        
        migrations.AddField(
            model_name='news',
            name='author',
            field=models.CharField(default='Cotakid', max_length=100, verbose_name='Tác giả'),
        ),
        
        # Update existing records
        migrations.RunPython(migrate_existing_news),
        
        # Remove old fields
        migrations.RemoveField(
            model_name='news',
            name='old_excerpt',
        ),
        
        migrations.RemoveField(
            model_name='news',
            name='old_is_published',
        ),
        
        # Update Meta options
        migrations.AlterModelOptions(
            name='news',
            options={'ordering': ['-published_at', '-created_at'], 'verbose_name': 'Tin tức', 'verbose_name_plural': 'Tin tức'},
        ),
        
        # Modify title field max_length
        migrations.AlterField(
            model_name='news',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Tiêu đề'),
        ),
    ]
