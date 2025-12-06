from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from products.models import Product
from .models import Cart, CartItem


def _get_session_cart(request):
    """Return dict mapping product_id -> qty stored in session"""
    return request.session.setdefault('cart', {})


def _get_or_create_user_cart(user):
    """Return the logged-in user's cart (create if missing)"""
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


def _merge_session_cart_to_user(request):
    """
    Convert items saved in session into DB cart items when a user logs in.
    """
    session_cart = request.session.get('cart', {})
    if not session_cart:
        return

    user_cart = _get_or_create_user_cart(request.user)

    for pid, qty in session_cart.items():
        product = Product.objects.filter(pk=pid).first()
        if not product:
            continue

        item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            product=product
        )
        if not created:
            item.quantity += qty
        else:
            item.quantity = qty
        item.save()

    # Clear session cart after merging
    request.session['cart'] = {}
    request.session.modified = True

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    qty = int(request.POST.get('quantity', 1))

    # 🔹 If user logged in: merge session cart once  
    if request.user.is_authenticated:
        _merge_session_cart_to_user(request)
        cart = _get_or_create_user_cart(request.user)

        obj, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            obj.quantity += qty
        else:
            obj.quantity = qty
        obj.save()

    else:
        # 🔹 GUEST CART in session
        cart = _get_session_cart(request)
        cart[str(product_id)] = cart.get(str(product_id), 0) + qty
        request.session.modified = True

    # Support AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'message': 'Added to cart'})

    return redirect('products:list')


def remove_from_cart(request, item_id):
    """
    item_id is the CartItem ID (for authenticated users)
    OR product_id (for session cart)
    """
    if request.user.is_authenticated:
        CartItem.objects.filter(id=item_id, cart__user=request.user).delete()
    else:
        cart = _get_session_cart(request)
        cart.pop(str(item_id), None)
        request.session.modified = True

    return redirect('cart:view_cart')


def view_cart(request):
    items = []
    total = 0

    # Authenticated user → DB cart
    if request.user.is_authenticated:
        _merge_session_cart_to_user(request)
        cart = _get_or_create_user_cart(request.user)
        qs = cart.items.select_related('product')

        for item in qs:
            items.append({
                'id': item.id,
                'product': item.product,
                'quantity': item.quantity,
                'line_total': item.line_total,
            })
            total += item.line_total

    else:
        # Guest user → session cart
        cart = _get_session_cart(request)
        product_ids = [int(pid) for pid in cart.keys()]
        products = Product.objects.filter(id__in=product_ids)
        prod_map = {p.id: p for p in products}

        for pid, qty in cart.items():
            product = prod_map.get(int(pid))
            if not product:
                continue
            line_total = qty * product.price
            items.append({
                'id': pid,                     # session uses pid
                'product': product,
                'quantity': qty,
                'line_total': line_total,
            })
            total += line_total

    return render(request, 'cart/cart_detail.html', {
        'items': items,
        'total': total
    })
