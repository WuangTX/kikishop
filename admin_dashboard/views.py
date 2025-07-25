from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils.text import slugify
from django.utils import timezone
from datetime import datetime, timedelta
from customer_web.models import Product, Category, Order, OrderItem, CustomerProfile, ProductInventory, ProductImage
from .models import News, DashboardSettings, NewsCategory
from .forms import NewsForm, NewsCategoryForm
from .inventory_forms import ProductInventoryForm, BulkInventoryForm
import json

# Check if user is admin/staff
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def generate_unique_sku(product, color, size):
    """Generate unique SKU for inventory item"""
    base_sku = f"{slugify(product.name)}-{slugify(color)}-{size}"
    sku = base_sku
    counter = 1
    
    # Ensure SKU is unique across all products
    while ProductInventory.objects.filter(sku=sku).exists():
        sku = f"{base_sku}-{counter}"
        counter += 1
    
    return sku

def process_product_images(request, product):
    """Xử lý upload và cập nhật ảnh sản phẩm"""
    try:
        # Xử lý ảnh được xóa
        images_to_delete = request.POST.getlist('images_to_delete')
        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete, product=product).delete()
        
        # Xử lý ảnh mới được upload
        uploaded_files = request.FILES.getlist('images')  # Từ input file thông thường
        new_images = request.FILES.getlist('new_images')  # Từ JavaScript processed files
        
        # Combine cả hai loại file
        all_files = uploaded_files + new_images
        
        if all_files:
            # Kiểm tra xem có ảnh chính hiện tại không
            has_primary = ProductImage.objects.filter(product=product, is_primary=True).exists()
            
            for i, image_file in enumerate(all_files):
                # Tạo ProductImage mới
                product_image = ProductImage(
                    product=product,
                    image=image_file,
                    alt_text=f'Ảnh sản phẩm {product.name} - {i+1}',
                    is_primary=(not has_primary and i == 0)  # Đặt ảnh đầu tiên làm primary nếu chưa có
                )
                product_image.save()
        
        # Xử lý việc đặt ảnh chính mới
        new_primary = request.POST.get('new_primary_image')
        if new_primary:
            # Reset tất cả ảnh cũ
            ProductImage.objects.filter(product=product).update(is_primary=False)
            # Set ảnh mới làm primary (tìm theo filename)
            try:
                new_image = ProductImage.objects.filter(
                    product=product, 
                    image__icontains=new_primary.split('.')[0]
                ).first()
                if new_image:
                    new_image.is_primary = True
                    new_image.save()
            except:
                pass
        
        # Xử lý việc cập nhật primary từ ảnh cũ
        old_primary = request.POST.get('primary_image')
        if old_primary:
            ProductImage.objects.filter(product=product).update(is_primary=False)
            ProductImage.objects.filter(id=old_primary, product=product).update(is_primary=True)
        
        # Cập nhật alt text cho ảnh cũ
        for key, value in request.POST.items():
            if key.startswith('alt_text_') and value:
                try:
                    image_id = key.replace('alt_text_', '')
                    if image_id.isdigit():
                        ProductImage.objects.filter(id=image_id, product=product).update(alt_text=value)
                except:
                    pass
                    
    except Exception as e:
        print(f"Error processing images: {str(e)}")  # Debug logging

def process_inventory_data(request, product):
    """Xử lý dữ liệu inventory từ form và cập nhật tồn kho"""
    try:
        # Lấy tất cả inventory data từ POST request
        inventory_data = {}
        for key, value in request.POST.items():
            if key.startswith('inventory[') and key.endswith('][quantity]'):
                # Parse key như: inventory[S][Đen][quantity]
                parts = key.replace('inventory[', '').replace('][quantity]', '').split('][')
                if len(parts) == 2:
                    size, color = parts
                    quantity = int(value) if value.isdigit() else 0
                    
                    # Lấy SKU nếu có
                    sku_key = f'inventory[{size}][{color}][sku]'
                    sku = request.POST.get(sku_key, '')
                    
                    inventory_data[f"{size}-{color}"] = {
                        'size': size,
                        'color': color,
                        'quantity': quantity,
                        'sku': sku
                    }
        
        # Xóa inventory cũ của sản phẩm này
        product.inventory.all().delete()
        
        # Tạo inventory mới
        for key, data in inventory_data.items():
            if data['quantity'] > 0:  # Chỉ tạo khi có số lượng > 0
                # Generate unique SKU if not provided or if it conflicts
                if not data['sku'] or ProductInventory.objects.filter(sku=data['sku']).exists():
                    data['sku'] = generate_unique_sku(product, data['color'], data['size'])
                
                ProductInventory.objects.create(
                    product=product,
                    size=data['size'],
                    color=data['color'],
                    quantity=data['quantity'],
                    sku=data['sku']
                )
        
        # Cập nhật stock tổng
        product.update_stock_from_inventory()
        
    except Exception as e:
        print(f"Error processing inventory data: {e}")
        pass  # Không làm crash form chính

@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    """Dashboard trang chủ với thống kê"""
    # Thống kê tổng quan
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = CustomerProfile.objects.count()
    total_revenue = Order.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # Đơn hàng gần đây
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Sản phẩm bán chạy
    bestsellers = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]
    
    # Thống kê theo tháng
    current_month = timezone.now().replace(day=1)
    monthly_orders = Order.objects.filter(created_at__gte=current_month).count()
    monthly_revenue = Order.objects.filter(
        created_at__gte=current_month,
        status='delivered'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'bestsellers': bestsellers,
        'monthly_orders': monthly_orders,
        'monthly_revenue': monthly_revenue,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def product_list(request):
    """Danh sách sản phẩm"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    products = Product.objects.prefetch_related('categories').order_by('-created_at')
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    if category_id.isdigit():
        products = products.filter(categories__id=int(category_id))

    
    categories = Category.objects.all()
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    return render(request, 'admin_dashboard/product_list.html', context)

@login_required
@user_passes_test(is_admin)
def product_add(request):
    """Thêm sản phẩm mới"""
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            name = request.POST.get('name')
            slug = slugify(name)
            category = request.POST.getlist('categories')
            description = request.POST.get('description')
            price = request.POST.get('price')
            discount_price = request.POST.get('discount_price')
            # Bỏ stock manual, sẽ tính từ inventory
            sizes = request.POST.get('sizes')
            colors = request.POST.get('colors')
            is_featured = request.POST.get('is_featured') == 'on'
            is_hot_trend = request.POST.get('is_hot_trend') == 'on'
            
            # Tạo sản phẩm với stock = 0 ban đầu
            product = Product.objects.create(
                name=name,
                slug=slug,
                description=description,
                price=price,
                discount_price=discount_price if discount_price else None,
                stock=0,  # Sẽ được cập nhật từ inventory
                sizes=sizes,
                colors=colors,
                is_featured=is_featured,
                is_hot_trend=is_hot_trend
            )
            # Xử lý nhiều danh mục
            product.categories.set(category)

            # Xử lý inventory data (nếu có)
            process_inventory_data(request, product)
            
            # Xử lý upload ảnh (nếu có)
            process_product_images(request, product)
            
            messages.success(request, f'Đã thêm sản phẩm "{name}" thành công!')
            return redirect('admin_dashboard:product_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm sản phẩm: {str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'admin_dashboard/product_form.html', {
        'categories': categories,
        'action': 'add'
    })

@login_required
@user_passes_test(is_admin)
def product_edit(request, product_id):
    """Chỉnh sửa sản phẩm"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.slug = slugify(product.name)
            # Xử lý nhiều danh mục
            category_ids = request.POST.getlist('categories')
            product.categories.clear()  # Xóa các danh mục cũ
            product.categories.add(*category_ids)  # Thêm các danh mục mới
            
            product.description = request.POST.get('description')
            product.price = request.POST.get('price')
            product.discount_price = request.POST.get('discount_price') or None
            # Bỏ cập nhật stock manual
            product.sizes = request.POST.get('sizes')
            product.colors = request.POST.get('colors')
            product.is_featured = request.POST.get('is_featured') == 'on'
            product.is_hot_trend = request.POST.get('is_hot_trend') == 'on'
            product.save()
            
            # Xử lý inventory data (nếu có)
            process_inventory_data(request, product)
            
            # Xử lý upload ảnh (nếu có)
            process_product_images(request, product)
            
            messages.success(request, f'Đã cập nhật sản phẩm "{product.name}" thành công!')
            return redirect('admin_dashboard:product_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật sản phẩm: {str(e)}')
    
    categories = Category.objects.all()
    # Lấy danh sách id của các danh mục hiện tại của sản phẩm
    product_category_ids = list(product.categories.values_list('id', flat=True))
    
    return render(request, 'admin_dashboard/product_form.html', {
        'product': product,
        'categories': categories,
        'product_category_ids': product_category_ids,
        'action': 'edit'
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def product_delete(request, product_id):
    """Xóa sản phẩm"""
    try:
        product = get_object_or_404(Product, id=product_id)
        product_name = product.name
        product.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Đã xóa sản phẩm "{product_name}"'})
        else:
            messages.success(request, f'Đã xóa sản phẩm "{product_name}" thành công!')
            return redirect('admin_dashboard:product_list')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
        else:
            messages.error(request, f'Lỗi khi xóa sản phẩm: {str(e)}')
            return redirect('admin_dashboard:product_list')

@login_required
@user_passes_test(is_admin)
def news_list(request):
    """Danh sách tin tức"""
    query = request.GET.get('q', '')
    
    news = News.objects.select_related('category').order_by('-created_at')
    
    if query:
        news = news.filter(
            Q(title__icontains=query) | Q(summary__icontains=query) | Q(content__icontains=query)
        )
    
    paginator = Paginator(news, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'admin_dashboard/news_list.html', context)

@login_required
@user_passes_test(is_admin)
def news_add(request):
    """Thêm tin tức mới"""
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save()
            messages.success(request, f'Đã thêm tin tức "{news.title}" thành công!')
            return redirect('admin_dashboard:news_list')
        else:
            messages.error(request, 'Có lỗi trong form. Vui lòng kiểm tra lại.')
    else:
        form = NewsForm()
    
    categories = NewsCategory.objects.all()
    context = {
        'form': form,
        'action': 'add',
        'categories': categories
    }
    return render(request, 'admin_dashboard/news_form.html', context)

@login_required
@user_passes_test(is_admin)
def news_edit(request, news_id):
    """Chỉnh sửa tin tức"""
    news = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            news = form.save()
            messages.success(request, f'Đã cập nhật tin tức "{news.title}" thành công!')
            return redirect('admin_dashboard:news_list')
        else:
            messages.error(request, 'Có lỗi trong form. Vui lòng kiểm tra lại.')
    else:
        form = NewsForm(instance=news)
    
    categories = NewsCategory.objects.all()
    context = {
        'form': form,
        'news': news,
        'action': 'edit',
        'categories': categories
    }
    return render(request, 'admin_dashboard/news_form.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def news_delete(request, news_id):
    """Xóa tin tức"""
    try:
        news = get_object_or_404(News, id=news_id)
        news_title = news.title
        news.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Đã xóa tin tức "{news_title}"'})
        else:
            messages.success(request, f'Đã xóa tin tức "{news_title}" thành công!')
            return redirect('admin_dashboard:news_list')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
        else:
            messages.error(request, f'Lỗi khi xóa tin tức: {str(e)}')
            return redirect('admin_dashboard:news_list')

@login_required
@user_passes_test(is_admin)
def order_list(request):
    """Danh sách đơn hàng"""
    status = request.GET.get('status', '')
    query = request.GET.get('q', '')
    
    orders = Order.objects.select_related('user').order_by('-created_at')
    
    if status:
        orders = orders.filter(status=status)
    
    if query:
        orders = orders.filter(
            Q(full_name__icontains=query) | 
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Tính toán thống kê theo trạng thái
    order_stats = {
        'pending': Order.objects.filter(status='pending').count(),
        'confirmed': Order.objects.filter(status='confirmed').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipping': Order.objects.filter(status='shipping').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
        'return_requested': Order.objects.filter(status='return_requested').count(),
        'return_approved': Order.objects.filter(status='return_approved').count(),
        'returned': Order.objects.filter(status='returned').count(),
        'refunded': Order.objects.filter(status='refunded').count(),
    }
    
    status_choices = Order.STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'status_choices': status_choices,
        'selected_status': status,
        'query': query,
        'order_stats': order_stats,
    }
    return render(request, 'admin_dashboard/order_list.html', context)

@login_required
@user_passes_test(is_admin)
def order_detail(request, order_id):
    """Chi tiết đơn hàng"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.select_related('product').all()
    
    if request.method == 'POST':
        action = request.POST.get('action', 'update_status')
        
        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(Order.STATUS_CHOICES):
                old_status = order.status
                order.status = new_status
                
                # Cập nhật thông tin hoàn trả tự động
                if new_status == 'return_requested' and old_status != 'return_requested':
                    order.return_requested_at = timezone.now()
                elif new_status == 'return_approved' and old_status != 'return_approved':
                    order.return_approved_at = timezone.now()
                elif new_status == 'returned' and old_status != 'returned':
                    order.return_completed_at = timezone.now()
                elif new_status == 'refunded' and old_status != 'refunded':
                    order.refund_completed_at = timezone.now()
                    if not order.refund_amount:
                        order.refund_amount = order.total_amount
                
                order.save()
                messages.success(request, f'Đã cập nhật trạng thái đơn hàng thành "{order.get_status_display()}"')
                return redirect('admin_dashboard:order_detail', order_id=order_id)
        
        elif action == 'update_return_info':
            order.return_reason = request.POST.get('return_reason', '')
            refund_amount = request.POST.get('refund_amount')
            if refund_amount:
                try:
                    order.refund_amount = float(refund_amount)
                except ValueError:
                    messages.error(request, 'Số tiền hoàn không hợp lệ')
                    return redirect('admin_dashboard:order_detail', order_id=order_id)
            
            order.save()
            messages.success(request, 'Đã cập nhật thông tin hoàn trả')
            return redirect('admin_dashboard:order_detail', order_id=order_id)
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_dashboard/order_detail.html', context)

@login_required
@user_passes_test(is_admin)
def bulk_order_action(request):
    """Xử lý bulk actions cho đơn hàng"""
    if request.method == 'POST':
        order_ids = request.POST.getlist('order_ids')
        action = request.POST.get('action')
        
        if not order_ids:
            messages.error(request, 'Vui lòng chọn ít nhất một đơn hàng')
            return redirect('admin_dashboard:order_list')
        
        orders = Order.objects.filter(id__in=order_ids)
        success_count = 0
        
        try:
            for order in orders:
                if action == 'mark_shipped':
                    if order.status in ['confirmed', 'processing']:
                        order.status = 'shipping'
                        order.save()
                        success_count += 1
                elif action == 'mark_delivered':
                    if order.status == 'shipping':
                        order.status = 'delivered'
                        order.save()
                        success_count += 1
                elif action == 'approve_returns':
                    if order.status == 'return_requested':
                        order.status = 'return_approved'
                        order.return_approved_at = timezone.now()
                        order.save()
                        success_count += 1
                elif action == 'mark_refunded':
                    if order.status in ['return_approved', 'returned']:
                        order.status = 'refunded'
                        order.refund_completed_at = timezone.now()
                        if not order.refund_amount:
                            order.refund_amount = order.total_amount
                        order.save()
                        success_count += 1
            
            if success_count > 0:
                messages.success(request, f'Đã cập nhật {success_count} đơn hàng thành công')
            else:
                messages.warning(request, 'Không có đơn hàng nào được cập nhật')
                
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    return redirect('admin_dashboard:order_list')

# Inventory Management Views
@login_required
@user_passes_test(is_admin)
def inventory_list(request):
    """Danh sách tồn kho sản phẩm"""
    query = request.GET.get('q', '')
    product_id = request.GET.get('product', '')
    size = request.GET.get('size', '')
    color = request.GET.get('color', '')
    stock_status = request.GET.get('stock_status', '')
    
    inventory = ProductInventory.objects.select_related('product').order_by('product__name', 'color', 'size')
    
    if query:
        inventory = inventory.filter(
            Q(product__name__icontains=query) | Q(sku__icontains=query)
        )
    
    if product_id:
        inventory = inventory.filter(product_id=product_id)
    
    if size:
        inventory = inventory.filter(size=size)
    
    if color:
        inventory = inventory.filter(color=color)
    
    if stock_status == 'out_of_stock':
        inventory = inventory.filter(quantity=0)
    elif stock_status == 'low_stock':
        inventory = inventory.filter(quantity__gt=0, quantity__lte=5)
    elif stock_status == 'in_stock':
        inventory = inventory.filter(quantity__gt=5)
    
    paginator = Paginator(inventory, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    products = Product.objects.filter(is_active=True).order_by('name')
    sizes = ProductInventory.SIZE_CHOICES
    colors = ProductInventory.COLOR_CHOICES
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_product': product_id,
        'selected_size': size,
        'selected_color': color,
        'selected_stock_status': stock_status,
        'products': products,
        'sizes': sizes,
        'colors': colors,
    }
    return render(request, 'admin_dashboard/inventory_list.html', context)

@login_required
@user_passes_test(is_admin)
def inventory_add(request):
    """Thêm tồn kho mới"""
    if request.method == 'POST':
        form = ProductInventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save()
            messages.success(request, f'Đã thêm tồn kho cho {inventory.product.name} - {inventory.get_color_display()} - {inventory.size}')
            return redirect('admin_dashboard:inventory_list')
        else:
            messages.error(request, 'Có lỗi trong form. Vui lòng kiểm tra lại.')
    else:
        form = ProductInventoryForm()
    
    context = {
        'form': form,
        'action': 'add',
    }
    return render(request, 'admin_dashboard/inventory_form.html', context)

@login_required
@user_passes_test(is_admin)
def inventory_edit(request, inventory_id):
    """Chỉnh sửa tồn kho"""
    inventory = get_object_or_404(ProductInventory, id=inventory_id)
    
    if request.method == 'POST':
        form = ProductInventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            inventory = form.save()
            messages.success(request, f'Đã cập nhật tồn kho cho {inventory.product.name} - {inventory.get_color_display()} - {inventory.size}')
            return redirect('admin_dashboard:inventory_list')
        else:
            messages.error(request, 'Có lỗi trong form. Vui lòng kiểm tra lại.')
    else:
        form = ProductInventoryForm(instance=inventory)
    
    context = {
        'form': form,
        'inventory': inventory,
        'action': 'edit',
    }
    return render(request, 'admin_dashboard/inventory_form.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def inventory_delete(request, inventory_id):
    """Xóa tồn kho"""
    try:
        inventory = get_object_or_404(ProductInventory, id=inventory_id)
        inventory_info = f"{inventory.product.name} - {inventory.get_color_display()} - {inventory.size}"
        inventory.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Đã xóa tồn kho {inventory_info}'})
        else:
            messages.success(request, f'Đã xóa tồn kho {inventory_info}')
            return redirect('admin_dashboard:inventory_list')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
        else:
            messages.error(request, f'Lỗi khi xóa tồn kho: {str(e)}')
            return redirect('admin_dashboard:inventory_list')

@login_required
@user_passes_test(is_admin)
def bulk_inventory(request):
    """Cập nhật tồn kho hàng loạt"""
    if request.method == 'POST':
        form = BulkInventoryForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            sizes = form.cleaned_data['sizes']
            colors = form.cleaned_data['colors']
            operation = form.cleaned_data['operation']
            quantity = form.cleaned_data['quantity']
            
            created_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            try:
                for size in sizes:
                    for color in colors:
                        try:
                            # Try to get existing inventory first
                            inventory = ProductInventory.objects.filter(
                                product=product,
                                size=size,
                                color=color
                            ).first()
                            
                            if inventory:
                                # Update existing inventory based on operation
                                if operation == 'set':
                                    inventory.quantity = quantity
                                elif operation == 'add':
                                    inventory.quantity += quantity
                                elif operation == 'subtract':
                                    inventory.quantity = max(0, inventory.quantity - quantity)  # Không để âm
                                
                                inventory.save()
                                updated_count += 1
                            else:
                                # Create new inventory (chỉ khi operation là 'set' hoặc 'add')
                                if operation in ['set', 'add']:
                                    # Generate unique SKU for new inventory
                                    sku = generate_unique_sku(product, color, size)
                                    
                                    new_quantity = quantity if operation == 'set' else quantity
                                    
                                    inventory = ProductInventory.objects.create(
                                        product=product,
                                        size=size,
                                        color=color,
                                        quantity=new_quantity,
                                        sku=sku
                                    )
                                    created_count += 1
                                else:
                                    # Không thể trừ từ inventory không tồn tại
                                    errors.append(f"Không thể trừ từ {size}-{color}: không tồn tại trong kho")
                                    error_count += 1
                                
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Lỗi với {size}-{color}: {str(e)}")
                            continue
                
                # Success message
                operation_text = {
                    'set': 'đặt thành',
                    'add': 'tăng thêm', 
                    'subtract': 'giảm đi'
                }.get(operation, 'cập nhật')
                
                success_msg = f'Đã {operation_text} {quantity} cho {created_count + updated_count} biến thể của {product.name}'
                if created_count > 0:
                    success_msg += f' (tạo mới: {created_count}, cập nhật: {updated_count})'
                if error_count > 0:
                    success_msg += f'. Có {error_count} lỗi xảy ra.'
                
                messages.success(request, success_msg)
                
                # Show errors if any
                if errors:
                    for error in errors[:5]:  # Show max 5 errors
                        messages.warning(request, error)
                
                return redirect('admin_dashboard:inventory_list')
                
            except Exception as e:
                messages.error(request, f'Lỗi hệ thống: {str(e)}')
                
        else:
            messages.error(request, 'Có lỗi trong form. Vui lòng kiểm tra lại.')
            
    else:
        form = BulkInventoryForm()
    
    context = {
        'form': form,
    }
    return render(request, 'admin_dashboard/bulk_inventory.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def check_inventory_conflicts(request):
    """Check for existing inventory conflicts via AJAX"""
    try:
        product_id = request.POST.get('product_id')
        sizes = request.POST.getlist('sizes')
        colors = request.POST.getlist('colors')
        
        if not all([product_id, sizes, colors]):
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        product = get_object_or_404(Product, id=product_id)
        
        conflicts = []
        new_items = []
        
        for size in sizes:
            for color in colors:
                existing = ProductInventory.objects.filter(
                    product=product,
                    size=size,
                    color=color
                ).first()
                
                if existing:
                    conflicts.append({
                        'size': size,
                        'color': color,
                        'current_quantity': existing.quantity,
                        'current_sku': existing.sku
                    })
                else:
                    preview_sku = generate_unique_sku(product, color, size)
                    new_items.append({
                        'size': size,
                        'color': color,
                        'preview_sku': preview_sku
                    })
        
        return JsonResponse({
            'conflicts': conflicts,
            'new_items': new_items,
            'total_conflicts': len(conflicts),
            'total_new': len(new_items)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ======================== CATEGORY MANAGEMENT ========================

@login_required
@user_passes_test(is_admin)
def category_list(request):
    """Danh sách danh mục sản phẩm"""
    search_query = request.GET.get('search', '')
    
    categories = Category.objects.all()
    
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    categories = categories.order_by('name')
    
    # Pagination
    paginator = Paginator(categories, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categories': page_obj,
        'search_query': search_query,
        'total_categories': categories.count(),
    }
    return render(request, 'admin_dashboard/category_list.html', context)

@login_required
@user_passes_test(is_admin)
def category_add(request):
    """Thêm danh mục mới"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            slug = slugify(name)
            description = request.POST.get('description')
            is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload
            image = request.FILES.get('image')
            
            # Check if slug already exists
            if Category.objects.filter(slug=slug).exists():
                messages.error(request, f'Danh mục với tên "{name}" đã tồn tại!')
                return render(request, 'admin_dashboard/category_form.html', {
                    'action': 'add',
                    'form_data': request.POST
                })
            
            category = Category.objects.create(
                name=name,
                slug=slug,
                description=description,
                image=image,
                is_active=is_active
            )
            
            messages.success(request, f'Đã thêm danh mục "{name}" thành công!')
            return redirect('admin_dashboard:category_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm danh mục: {str(e)}')
    
    return render(request, 'admin_dashboard/category_form.html', {
        'action': 'add'
    })

@login_required
@user_passes_test(is_admin)
def category_edit(request, category_id):
    """Chỉnh sửa danh mục"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            old_name = category.name
            category.name = request.POST.get('name')
            category.slug = slugify(category.name)
            category.description = request.POST.get('description')
            category.is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload
            if request.FILES.get('image'):
                category.image = request.FILES.get('image')
            
            # Check if new slug conflicts with other categories
            if Category.objects.filter(slug=category.slug).exclude(id=category.id).exists():
                messages.error(request, f'Danh mục với tên "{category.name}" đã tồn tại!')
                return render(request, 'admin_dashboard/category_form.html', {
                    'category': category,
                    'action': 'edit'
                })
            
            category.save()
            
            messages.success(request, f'Đã cập nhật danh mục "{category.name}" thành công!')
            return redirect('admin_dashboard:category_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật danh mục: {str(e)}')
    
    return render(request, 'admin_dashboard/category_form.html', {
        'category': category,
        'action': 'edit'
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def category_delete(request, category_id):
    """Xóa danh mục"""
    try:
        category = get_object_or_404(Category, id=category_id)
        
        # Check if category has products
        product_count = category.products.count()
        if product_count > 0:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': f'Không thể xóa danh mục "{category.name}" vì có {product_count} sản phẩm đang sử dụng!'
                })
            else:
                messages.error(request, f'Không thể xóa danh mục "{category.name}" vì có {product_count} sản phẩm đang sử dụng!')
                return redirect('admin_dashboard:category_list')
        
        category_name = category.name
        category.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Đã xóa danh mục "{category_name}" thành công!'})
        else:
            messages.success(request, f'Đã xóa danh mục "{category_name}" thành công!')
            return redirect('admin_dashboard:category_list')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
        else:
            messages.error(request, f'Lỗi khi xóa danh mục: {str(e)}')
            return redirect('admin_dashboard:category_list')

@login_required
@user_passes_test(is_admin)
@require_POST
def category_toggle_status(request, category_id):
    """Bật/tắt trạng thái danh mục"""
    try:
        category = get_object_or_404(Category, id=category_id)
        category.is_active = not category.is_active
        category.save()
        
        status_text = "kích hoạt" if category.is_active else "vô hiệu hóa"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': f'Đã {status_text} danh mục "{category.name}"',
                'is_active': category.is_active
            })
        else:
            messages.success(request, f'Đã {status_text} danh mục "{category.name}"')
            return redirect('admin_dashboard:category_list')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': f'Lỗi: {str(e)}'})
        else:
            messages.error(request, f'Lỗi: {str(e)}')
            return redirect('admin_dashboard:category_list')
