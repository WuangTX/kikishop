from django.urls import path
from . import views

app_name = 'customer_web'

urlpatterns = [
    # Home and products
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Cart functionality
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    
    # Product inventory API
    path('api/product/<int:product_id>/inventory/', views.get_product_inventory, name='get_product_inventory'),
    
    # User authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Checkout and orders
    path('checkout/', views.checkout_view, name='checkout'),
    path('order-success/<uuid:order_id>/', views.order_success, name='order_success'),
    path('order-history/', views.order_history, name='order_history'),
    
    # News
    path('news/', views.news_list, name='news_list'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
]
