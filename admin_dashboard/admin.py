from django.contrib import admin
from .models import News, DashboardSettings, NewsCategory

@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'featured', 'views', 'published_at']
    list_filter = ['status', 'featured', 'category', 'created_at']
    search_fields = ['title', 'summary', 'content', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('category', 'title', 'slug', 'summary', 'content')
        }),
        ('Hình ảnh', {
            'fields': ('image', 'image_position', 'image_caption')
        }),
        ('Liên kết và thẻ', {
            'fields': ('external_link', 'external_link_text', 'tags')
        }),
        ('Cài đặt xuất bản', {
            'fields': ('status', 'featured', 'author', 'published_at')
        }),
        ('Thống kê', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DashboardSettings)
class DashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'maintenance_mode', 'allow_registrations', 'updated_by', 'updated_at']
    fields = ['site_name', 'site_logo', 'maintenance_mode', 'allow_registrations']
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
