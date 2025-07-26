from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
import json

from .models import (
    Category, Product, ProductImage, CustomerProfile, 
    Cart, CartItem, Order, OrderItem
)
from admin_dashboard.models import News

def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart

# Home page
def home(request):
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    hot_trend_products = Product.objects.filter(is_hot_trend=True, is_active=True)[:8]
    new_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)
    featured_news = News.objects.filter(status='published', featured=True)[:3]
    
    context = {
        'featured_products': featured_products,
        'hot_trend_products': hot_trend_products,
        'new_products': new_products,
        'categories': categories,
        'featured_news': featured_news,
    }
    return render(request, 'customer_web/home.html', context)

# Product listing
def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    
    # Filter by categories
    category_slugs = request.GET.get('categories', '')
    selected_categories = []
    if category_slugs:
        q = Q()
        for slug in category_slugs.split(','):
            selected_categories.append(slug)
            q |= Q(categories__slug=slug)  # dùng toán tử OR
        products = products.filter(q).distinct()
    # Search
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Sort
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'trending':
        products = products.filter(is_hot_trend=True).order_by('-created_at')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'selected_categories': selected_categories,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'customer_web/product_list.html', context)

# Product detail
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    # Lấy danh mục đầu tiên (nếu có) để gợi ý sản phẩm liên quan
    first_category = product.categories.first()
    if first_category:
        related_products = Product.objects.filter(
            categories=first_category,
            is_active=True
        ).exclude(id=product.id)[:4]
    else:
        related_products = Product.objects.filter(is_active=True).exclude(id=product.id)[:4]
    
    # Convert sizes and colors from string to list
    sizes_list = [size.strip() for size in product.sizes.split(',') if size.strip()] if product.sizes else []
    colors_list = [color.strip() for color in product.colors.split(',') if color.strip()] if product.colors else []
    
    # Get inventory data for size and color combinations
    inventory_data = {}
    if sizes_list and colors_list:
        inventory_items = product.inventory.all()
        for item in inventory_items:
            key = f"{item.size}-{item.color}"
            inventory_data[key] = item.quantity
    
    context = {
        'product': product,
        'related_products': related_products,
        'sizes_list': sizes_list,
        'colors_list': colors_list,
        'inventory_data': json.dumps(inventory_data),
    }
    return render(request, 'customer_web/product_detail.html', context)

# API endpoint to get inventory info
@csrf_exempt
def get_product_inventory(request, product_id):
    """API để lấy thông tin tồn kho theo size và màu"""
    if request.method == 'GET':
        try:
            product = get_object_or_404(Product, id=product_id)
            size = request.GET.get('size', '')
            color = request.GET.get('color', '')
            
            # If both size and color are provided, get specific inventory
            if size and color:
                try:
                    inventory = product.inventory.get(size=size, color=color)
                    return JsonResponse({
                        'success': True,
                        'quantity': inventory.quantity,
                        'sku': inventory.sku
                    })
                except:
                    return JsonResponse({
                        'success': True,
                        'quantity': 0,
                        'sku': ''
                    })
            
            # If only size or color is provided, get all matching combinations
            elif size or color:
                inventory_items = product.inventory.all()
                if size:
                    inventory_items = inventory_items.filter(size=size)
                if color:
                    inventory_items = inventory_items.filter(color=color)
                
                total_quantity = sum(item.quantity for item in inventory_items)
                items_data = []
                for item in inventory_items:
                    items_data.append({
                        'size': item.size,
                        'color': item.color,
                        'quantity': item.quantity,
                        'sku': item.sku
                    })
                
                return JsonResponse({
                    'success': True,
                    'total_quantity': total_quantity,
                    'items': items_data
                })
            
            # Return all inventory for the product
            else:
                inventory_items = product.inventory.all()
                inventory_data = {}
                for item in inventory_items:
                    key = f"{item.size}-{item.color}"
                    inventory_data[key] = {
                        'quantity': item.quantity,
                        'sku': item.sku
                    }
                
                return JsonResponse({
                    'success': True,
                    'inventory': inventory_data
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Add to cart
@csrf_exempt
def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            size = data.get('size', '')
            color = data.get('color', '')
            quantity = int(data.get('quantity', 1))
            
            product = get_object_or_404(Product, id=product_id)
            cart = get_or_create_cart(request)
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=size,
                color=color,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Đã thêm vào giỏ hàng',
                'cart_total': cart.total_items
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})


@csrf_exempt
def get_cart_total(request):
    try:
        cart = get_or_create_cart(request)
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_items
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
# Cart view
def cart_view(request):
    cart = get_or_create_cart(request)
    context = {
        'cart': cart,
    }
    return render(request, 'customer_web/cart.html', context)

# Update cart item
@csrf_exempt
def update_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity'))
            
            cart_item = get_object_or_404(CartItem, id=item_id)
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
            
            cart = cart_item.cart
            return JsonResponse({
                'success': True,
                'cart_total': cart.total_items,
                'cart_price': float(cart.total_price)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

# Remove from cart
@csrf_exempt
def remove_from_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            cart_item = get_object_or_404(CartItem, id=item_id)
            cart = cart_item.cart
            cart_item.delete()
            
            return JsonResponse({
                'success': True,
                'cart_total': cart.total_items,
                'cart_price': float(cart.total_price)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

# User authentication views
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Merge guest cart with user cart
            guest_cart = None
            if request.session.session_key:
                try:
                    guest_cart = Cart.objects.get(session_key=request.session.session_key)
                except Cart.DoesNotExist:
                    pass
            
            if guest_cart:
                user_cart, created = Cart.objects.get_or_create(user=user)
                # Move items from guest cart to user cart
                for item in guest_cart.items.all():
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=user_cart,
                        product=item.product,
                        size=item.size,
                        color=item.color,
                        defaults={'quantity': item.quantity}
                    )
                    if not created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                guest_cart.delete()
            
            # Đăng nhập thành công - không hiển thị thông báo
            return redirect('customer_web:home')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')
    
    return render(request, 'customer_web/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp!')
            return render(request, 'customer_web/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tên đăng nhập đã tồn tại!')
            return render(request, 'customer_web/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email đã được sử dụng!')
            return render(request, 'customer_web/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create customer profile
        CustomerProfile.objects.create(user=user)
        
        messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
        return redirect('customer_web:login')
    
    return render(request, 'customer_web/register.html')

def logout_view(request):
    logout(request)
    # Đăng xuất thành công - không hiển thị thông báo
    return redirect('customer_web:home')

# User profile
@login_required
def profile_view(request):
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        
        # Update profile
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.gender = request.POST.get('gender')
        profile.save()
        
        messages.success(request, 'Cập nhật thông tin thành công!')
    
    context = {
        'profile': profile,
    }
    return render(request, 'customer_web/profile.html', context)

# Checkout
def checkout_view(request):
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.error(request, 'Giỏ hàng trống!')
        return redirect('customer_web:cart')
    
    if request.method == 'POST':
        # Create order
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        notes = request.POST.get('notes', '')
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_email=email if not request.user.is_authenticated else None,
            guest_phone=phone if not request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            total_amount=cart.total_price,
            notes=notes
        )
        
        # Create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                size=item.size,
                color=item.color,
                quantity=item.quantity,
                price=item.product.get_price
            )
            
            # Update stock
            item.product.stock -= item.quantity
            item.product.save()
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, f'Đặt hàng thành công! Mã đơn hàng: {order.order_id.hex[:8]}')
        return redirect('customer_web:order_success', order_id=order.order_id)
    
    context = {
        'cart': cart,
    }
    return render(request, 'customer_web/checkout.html', context)

# Order success
def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'customer_web/order_success.html', context)

# Order history
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'customer_web/order_history.html', context)

# News views
def news_list(request):
    """Danh sách tin tức"""
    news = News.objects.filter(status='published').order_by('-published_at')
    
    # Search
    query = request.GET.get('search', '')
    if query:
        news = news.filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(news, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'news_list': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'query': query,
    }
    return render(request, 'customer_web/news_list.html', context)

def news_detail(request, slug):
    """Chi tiết tin tức"""
    news = get_object_or_404(News, slug=slug, status='published')
    
    # Tăng lượt xem
    news.views += 1
    news.save()
    
    # Tin tức liên quan
    related_news = News.objects.filter(
        status='published'
    ).exclude(id=news.id).order_by('-published_at')[:4]
    
    context = {
        'news': news,
        'related_news': related_news,
    }
    return render(request, 'customer_web/news_detail.html', context)
