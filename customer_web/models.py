from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

# Category model for fashion products
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"
        ordering = ['name']
    
    def __str__(self):
        return self.name

# Product model for Korean fashion items
class Product(models.Model):
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    
    COLOR_CHOICES = [
        ('white', 'Trắng'),
        ('black', 'Đen'),
        ('gray', 'Xám'),
        ('beige', 'Be'),
        ('pink', 'Hồng'),
        ('blue', 'Xanh dương'),
        ('navy', 'Navy'),
        ('brown', 'Nâu'),
        ('red', 'Đỏ'),
        ('yellow', 'Vàng'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(verbose_name="Mô tả")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá")
    discount_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="Giá khuyến mãi")
    stock = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    sizes = models.CharField(max_length=50, help_text="Các size có sẵn, cách nhau bởi dấu phẩy")
    colors = models.CharField(max_length=100, help_text="Các màu có sẵn, cách nhau bởi dấu phẩy")
    is_featured = models.BooleanField(default=False, verbose_name="Sản phẩm nổi bật")
    is_hot_trend = models.BooleanField(default=False, verbose_name="Sản phẩm Hot Trend")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def get_price(self):
        return self.discount_price if self.discount_price else self.price
    
    @property
    def is_on_sale(self):
        return self.discount_price is not None
    
    @property
    def total_inventory_stock(self):
        """Tính tổng tồn kho từ các variant size/màu"""
        return self.inventory.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    def update_stock_from_inventory(self):
        """Cập nhật stock từ tổng inventory"""
        self.stock = self.total_inventory_stock
        self.save(update_fields=['stock'])

# Product images
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Hình ảnh sản phẩm"
        verbose_name_plural = "Hình ảnh sản phẩm"

# Customer profile
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Nam'), ('F', 'Nữ')], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Hồ sơ khách hàng"
        verbose_name_plural = "Hồ sơ khách hàng"
    
    def __str__(self):
        return f"{self.user.username} - {self.user.first_name} {self.user.last_name}"

# Cart for logged-in users
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=50, blank=True, null=True)  # For guest users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Giỏ hàng"
        verbose_name_plural = "Giỏ hàng"
    
    def __str__(self):
        if self.user:
            return f"Giỏ hàng của {self.user.username}"
        return f"Giỏ hàng khách - {self.session_key}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

# Cart items
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, blank=True)
    color = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sản phẩm trong giỏ"
        verbose_name_plural = "Sản phẩm trong giỏ"
        unique_together = ['cart', 'product', 'size', 'color']
    
    def __str__(self):
        return f"{self.product.name} - {self.size} - {self.color} x{self.quantity}"
    
    @property
    def total_price(self):
        return self.product.get_price * self.quantity

# Order model
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('confirmed', 'Đã xác nhận'),
        ('processing', 'Đang xử lý'),
        ('shipping', 'Đang giao'),
        ('delivered', 'Đã giao'),
        ('cancelled', 'Đã hủy'),
        ('return_requested', 'Yêu cầu hoàn trả'),
        ('return_approved', 'Đã duyệt hoàn trả'),
        ('returned', 'Đã hoàn trả'),
        ('refunded', 'Đã hoàn tiền'),
    ]
    
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)  # For guest orders
    guest_phone = models.CharField(max_length=15, blank=True, null=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=0)
    notes = models.TextField(blank=True)
    
    # Thông tin hoàn trả
    return_reason = models.TextField(blank=True, verbose_name="Lý do hoàn trả")
    return_requested_at = models.DateTimeField(blank=True, null=True, verbose_name="Ngày yêu cầu hoàn trả")
    return_approved_at = models.DateTimeField(blank=True, null=True, verbose_name="Ngày duyệt hoàn trả")
    return_completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Ngày hoàn trả hoàn tất")
    refund_amount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="Số tiền hoàn")
    refund_completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Ngày hoàn tiền")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Đơn hàng #{self.order_id.hex[:8]} - {self.full_name}"

# Order items
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5, blank=True)
    color = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0)  # Price at time of order
    
    class Meta:
        verbose_name = "Sản phẩm trong đơn hàng"
        verbose_name_plural = "Sản phẩm trong đơn hàng"
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    @property
    def total_price(self):
        return self.price * self.quantity


# Product Inventory - Quản lý tồn kho theo size và màu
class ProductInventory(models.Model):
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    
    COLOR_CHOICES = [
        ('white', 'Trắng'),
        ('black', 'Đen'),
        ('gray', 'Xám'),
        ('beige', 'Be'),
        ('pink', 'Hồng'),
        ('blue', 'Xanh dương'),
        ('navy', 'Navy'),
        ('brown', 'Nâu'),
        ('red', 'Đỏ'),
        ('yellow', 'Vàng'),
        ('green', 'Xanh lá'),
        ('purple', 'Tím'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, verbose_name="Size")
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, verbose_name="Màu sắc")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU", help_text="Mã sản phẩm theo size và màu")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tồn kho sản phẩm"
        verbose_name_plural = "Tồn kho sản phẩm"
        unique_together = ('product', 'size', 'color')
        ordering = ['product', 'color', 'size']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_color_display()} - {self.size} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            color_code = self.color[:3].upper()
            self.sku = f"{self.product.slug}-{color_code}-{self.size}".replace(' ', '-')
        super().save(*args, **kwargs)
    
    @property
    def is_in_stock(self):
        return self.quantity > 0
    
    @property
    def is_low_stock(self):
        return 0 < self.quantity <= 5
