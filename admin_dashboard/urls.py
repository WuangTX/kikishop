from django.urls import path
from . import views
from . import views_test

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard test
    path('test/', views_test.dashboard_home, name='dashboard_test'),
    
    # Dashboard chính
    path('', views.dashboard_home, name='dashboard_home'),
    
    # Quản lý sản phẩm
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # Quản lý danh mục
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('categories/<int:category_id>/toggle/', views.category_toggle_status, name='category_toggle_status'),
    
    # Quản lý tin tức
    path('news/', views.news_list, name='news_list'),
    path('news/add/', views.news_add, name='news_add'),
    path('news/<int:news_id>/edit/', views.news_edit, name='news_edit'),
    path('news/<int:news_id>/delete/', views.news_delete, name='news_delete'),
    
    # Quản lý đơn hàng
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/bulk-action/', views.bulk_order_action, name='bulk_order_action'),
    
    # Quản lý tồn kho
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_add, name='inventory_add'),
    path('inventory/<int:inventory_id>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:inventory_id>/delete/', views.inventory_delete, name='inventory_delete'),
    path('inventory/bulk/', views.bulk_inventory, name='bulk_inventory'),
    path('inventory/check-conflicts/', views.check_inventory_conflicts, name='check_inventory_conflicts'),
]
