from django.contrib import admin
from .models import (
    Category, Product, ProductImage, ProductInventory, CustomerProfile, 
    Cart, CartItem, Order, OrderItem
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductInventoryInline(admin.TabularInline):
    model = ProductInventory
    extra = 0
    fields = ['size', 'color', 'quantity', 'sku']
    readonly_fields = ['sku']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def categories_display(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    categories_display.short_description = 'Danh mục'

    list_display = ['name', 'categories_display', 'price', 'discount_price', 'stock', 'is_featured', 'is_active']
    list_filter = ['categories', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductInventoryInline]
    list_editable = ['price', 'discount_price', 'stock', 'is_featured', 'is_active']

@admin.register(ProductInventory)
class ProductInventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'color', 'quantity', 'sku', 'is_in_stock', 'is_low_stock']
    list_filter = ['size', 'color', 'product__categories']
    search_fields = ['product__name', 'sku']
    list_editable = ['quantity']
    readonly_fields = ['sku', 'created_at', 'updated_at']
    
    def is_in_stock(self, obj):
        return obj.is_in_stock
    is_in_stock.boolean = True
    is_in_stock.short_description = 'Còn hàng'
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Sắp hết hàng'

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'is_primary']
    list_filter = ['is_primary']

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'gender', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'total_items', 'total_price', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'session_key']
    inlines = [CartItemInline]

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'size', 'color', 'quantity', 'total_price']
    list_filter = ['added_at']
    search_fields = ['product__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'full_name', 'email', 'phone', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'full_name', 'email', 'phone']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['order_id']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'size', 'color', 'quantity', 'price', 'total_price']
    list_filter = ['order__created_at']
    search_fields = ['order__order_id', 'product__name']
