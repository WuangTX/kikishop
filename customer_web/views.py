from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import json

from .models import (
    Category, Product, ProductImage, ProductInventory, CustomerProfile, 
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
            
            # Return all variants for the product (for modal)
            else:
                inventory_items = product.inventory.all()
                variants = []
                for item in inventory_items:
                    variants.append({
                        'size': item.size,
                        'color': item.color,
                        'quantity': item.quantity,
                        'sku': item.sku
                    })
                
                return JsonResponse({
                    'success': True,
                    'variants': variants
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
            size = data.get('size', None)
            color = data.get('color', None)
            try:
                quantity = max(1, int(data.get('quantity', 1)))
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'message': 'Số lượng không hợp lệ'})
            
            # Validate required fields
            if not size:
                return JsonResponse({'success': False, 'message': 'Vui lòng chọn kích thước'})
            
            product = get_object_or_404(Product, id=product_id)
            cart = get_or_create_cart(request)
            
            # Check inventory
            from customer_web.models import ProductInventory
            try:
                inventory = ProductInventory.objects.get(
                    product=product,
                    size=size,
                    color=color or ''
                )
                if inventory.quantity < quantity:
                    return JsonResponse({
                        'success': False, 
                        'message': f'Chỉ còn {inventory.quantity} sản phẩm trong kho'
                    })
            except ProductInventory.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Sản phẩm không có sẵn với thông số này'})
            
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
                'cart_total_items': cart.total_items
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
    
    # Get user profile for auto-fill if authenticated
    user_profile = None
    if request.user.is_authenticated:
        user_profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Create order
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        notes = request.POST.get('notes', '')
        payment_method = request.POST.get('payment_method', 'cod')
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_email=email if not request.user.is_authenticated else None,
            guest_phone=phone if not request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            payment_method=payment_method,
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
            
            # Update ProductInventory instead of Product.stock
            try:
                inventory = ProductInventory.objects.get(
                    product=item.product,
                    size=item.size,
                    color=item.color
                )
                inventory.quantity -= item.quantity
                inventory.save()
            except ProductInventory.DoesNotExist:
                # Create new inventory with 0 quantity (deficit)
                from admin_dashboard.views import generate_unique_sku
                sku = generate_unique_sku(item.product, item.color, item.size)
                ProductInventory.objects.create(
                    product=item.product,
                    size=item.size,
                    color=item.color,
                    quantity=-item.quantity,  # Negative to indicate deficit
                    sku=sku
                )
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, f'Đặt hàng thành công! Mã đơn hàng: {order.order_id.hex[:8]}')
        return redirect('customer_web:order_success', order_id=order.order_id)
    
    context = {
        'cart': cart,
        'user_profile': user_profile,
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

# Cancel order
@login_required
@csrf_exempt
def cancel_order(request, order_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reason = data.get('reason', '')
            other_reason = data.get('other_reason', '')
            
            order = get_object_or_404(Order, order_id=order_id, user=request.user)
            
            # Check if order can be cancelled
            if order.status not in ['pending', 'confirmed']:
                return JsonResponse({
                    'success': False,
                    'message': 'Đơn hàng này không thể hủy'
                })
            
            # Prepare cancel reason text
            cancel_reason_text = reason
            if reason == 'other' and other_reason:
                cancel_reason_text = f"Lý do khác: {other_reason}"
            elif reason == 'changed_mind':
                cancel_reason_text = "Đổi ý không muốn mua"
            elif reason == 'found_better_price':
                cancel_reason_text = "Tìm được giá tốt hơn"
            elif reason == 'ordered_wrong':
                cancel_reason_text = "Đặt nhầm sản phẩm"
            elif reason == 'delivery_too_long':
                cancel_reason_text = "Thời gian giao hàng quá lâu"
            
            # Update order status
            order.status = 'cancelled'
            order.cancel_reason = cancel_reason_text
            order.cancelled_at = timezone.now()
            order.save()
            
            # Restore ProductInventory stock
            for item in order.items.all():
                try:
                    inventory = ProductInventory.objects.get(
                        product=item.product,
                        size=item.size,
                        color=item.color
                    )
                    inventory.quantity += item.quantity
                    inventory.save()
                except ProductInventory.DoesNotExist:
                    # Create new inventory if not exists
                    from admin_dashboard.views import generate_unique_sku
                    sku = generate_unique_sku(item.product, item.color, item.size)
                    ProductInventory.objects.create(
                        product=item.product,
                        size=item.size,
                        color=item.color,
                        quantity=item.quantity,
                        sku=sku
                    )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

# Request return
@login_required
@csrf_exempt
def request_return(request, order_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reason = data.get('reason', '')
            other_reason = data.get('other_reason', '')
            description = data.get('description', '')
            
            order = get_object_or_404(Order, order_id=order_id, user=request.user)
            
            # Check if order can be returned
            if order.status != 'delivered':
                return JsonResponse({
                    'success': False,
                    'message': 'Chỉ có thể yêu cầu hoàn trả đơn hàng đã giao'
                })
            
            # Check 7-day limit on server side as well
            days_since_order = (timezone.now() - order.created_at).days
            if days_since_order > 7:
                return JsonResponse({
                    'success': False,
                    'message': 'Đã hết hạn yêu cầu hoàn hàng. Thời gian hoàn trả chỉ có hiệu lực trong vòng 7 ngày.'
                })
            
            # Prepare return reason text
            return_reason_text = reason
            if reason == 'other' and other_reason:
                return_reason_text = f"Lý do khác: {other_reason}"
            elif reason == 'defective':
                return_reason_text = "Sản phẩm bị lỗi/hư hỏng"
            elif reason == 'wrong_item':
                return_reason_text = "Gửi sai sản phẩm"
            elif reason == 'not_as_described':
                return_reason_text = "Sản phẩm không đúng mô tả"
            elif reason == 'size_issue':
                return_reason_text = "Sai size/không vừa"
            elif reason == 'quality_issue':
                return_reason_text = "Chất lượng không như mong đợi"
            elif reason == 'changed_mind':
                return_reason_text = "Đổi ý không muốn sản phẩm"
            
            # Combine reason and description
            full_return_reason = f"{return_reason_text}\nMô tả chi tiết: {description}"
            
            # Update order status and save return info
            order.status = 'return_requested'
            order.return_reason = full_return_reason
            order.return_requested_at = timezone.now()
            order.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

# Reorder items from previous order
@login_required
@csrf_exempt
def reorder_items(request, order_id):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, order_id=order_id, user=request.user)
            
            # Check if order is delivered (only delivered orders can be reordered)
            if order.status != 'delivered':
                return JsonResponse({
                    'success': False,
                    'message': 'Chỉ có thể mua lại đơn hàng đã giao thành công'
                })
            
            # Get or create cart for user
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            items_added = 0
            items_skipped = 0
            
            # Add each order item to cart
            for order_item in order.items.all():
                # Check if product is still active and available
                if not order_item.product.is_active:
                    items_skipped += 1
                    continue
                
                # Check if there's enough inventory
                try:
                    inventory = ProductInventory.objects.get(
                        product=order_item.product,
                        size=order_item.size,
                        color=order_item.color
                    )
                    if inventory.quantity < order_item.quantity:
                        items_skipped += 1
                        continue
                except ProductInventory.DoesNotExist:
                    items_skipped += 1
                    continue
                
                # Check if item already exists in cart
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=order_item.product,
                    size=order_item.size,
                    color=order_item.color,
                    defaults={'quantity': order_item.quantity}
                )
                
                if not item_created:
                    # If item exists, increase quantity
                    cart_item.quantity += order_item.quantity
                    cart_item.save()
                
                items_added += 1
            
            message = f'Đã thêm {items_added} sản phẩm vào giỏ hàng!'
            if items_skipped > 0:
                message += f' ({items_skipped} sản phẩm không khả dụng)'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'items_count': items_added,
                'cart_total_items': cart.total_items
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})

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
