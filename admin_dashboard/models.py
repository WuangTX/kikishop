from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from customer_web.models import Product, Category


def news_image_upload_to(instance, filename):
    """Generate upload path for news images"""
    return f'news/{instance.slug}/{filename}'


class NewsCategory(models.Model):
    """Category for news articles"""
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Mô tả")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Danh mục tin tức"
        verbose_name_plural = "Danh mục tin tức"
        ordering = ['name']


# News/Blog model for admin dashboard
class News(models.Model):
    """Model for news articles"""
    IMAGE_POSITION_CHOICES = (
        ('left', 'Bên trái'),
        ('right', 'Bên phải'),
        ('top', 'Phía trên'),
        ('full', 'Toàn màn hình'),
        ('center', 'Giữa bài viết'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Bản nháp'),
        ('published', 'Đã xuất bản'),
        ('archived', 'Lưu trữ'),
    )
    
    category = models.ForeignKey(NewsCategory, on_delete=models.CASCADE, related_name="news", verbose_name="Danh mục", null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name="Tiêu đề")
    slug = models.SlugField(unique=True, blank=True)
    summary = models.TextField(max_length=500, verbose_name="Tóm tắt", help_text="Mô tả ngắn về bài viết (tối đa 500 ký tự)")
    content = models.TextField(verbose_name="Nội dung")
    image = models.ImageField(upload_to=news_image_upload_to, verbose_name="Hình ảnh chính", null=True, blank=True)
    image_position = models.CharField(max_length=10, choices=IMAGE_POSITION_CHOICES, default='top', verbose_name="Vị trí hình ảnh")
    image_caption = models.CharField(max_length=200, blank=True, verbose_name="Chú thích hình ảnh")
    external_link = models.URLField(blank=True, verbose_name="Liên kết ngoài", help_text="Link tham khảo hoặc nguồn tin")
    external_link_text = models.CharField(max_length=100, blank=True, verbose_name="Văn bản liên kết", help_text="Văn bản hiển thị cho liên kết ngoài")
    tags = models.CharField(max_length=255, blank=True, verbose_name="Thẻ", help_text="Các thẻ phân cách bằng dấu phẩy")
    featured = models.BooleanField(default=False, verbose_name="Tin nổi bật")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published', verbose_name="Trạng thái")
    author = models.CharField(max_length=100, default='KiKi', verbose_name="Tác giả")
    views = models.PositiveIntegerField(default=0, verbose_name="Lượt xem")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Ngày xuất bản")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Handle duplicate slugs
            original_slug = self.slug
            counter = 1
            while News.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Tin tức"
        verbose_name_plural = "Tin tức"
        ordering = ['-published_at', '-created_at']

# Dashboard Settings
class DashboardSettings(models.Model):
    site_name = models.CharField(max_length=100, default="CotoKid Admin")
    site_logo = models.ImageField(upload_to='dashboard/', blank=True, null=True)
    maintenance_mode = models.BooleanField(default=False)
    allow_registrations = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cài đặt Dashboard"
        verbose_name_plural = "Cài đặt Dashboard"
    
    def __str__(self):
        return self.site_name
