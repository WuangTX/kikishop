from customer_web.models import Cart

def cart_total_items(request):
    cart = None
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
            except Cart.DoesNotExist:
                pass
    total_items = cart.total_items if cart else 0
    return {'cart_total_items': total_items}
