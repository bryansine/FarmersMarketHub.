from .models import Cart, CartItem
from products.models import Product
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404


def _get_session_cart(request):
    return request.session.setdefault('cart', {})


def _get_or_create_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


def _merge_session_cart_to_user(request):
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
        item.quantity = item.quantity + qty if not created else qty
        item.save()

    request.session['cart'] = {}
    request.session.modified = True



def add_to_cart(request, product_id):
    """Add product to cart. Redirect to cart OR checkout depending on button."""
    product = get_object_or_404(Product, pk=product_id)
    qty = int(request.POST.get('quantity', 1))
    buy_now = request.POST.get('buy_now') == "1"

    if request.user.is_authenticated:
        _merge_session_cart_to_user(request)
        cart = _get_or_create_user_cart(request.user)

        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        item.quantity = item.quantity + qty if not created else qty
        item.save()

    else:
        cart = _get_session_cart(request)
        cart[str(product_id)] = cart.get(str(product_id), 0) + qty
        request.session.modified = True

    if buy_now:
        return redirect('orders:checkout')

    return redirect('cart:view_cart')



def remove_from_cart(request, item_id):
    """Remove cart item for logged in user OR session."""
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
                'id': pid,
                'product': product,
                'quantity': qty,
                'line_total': line_total,
            })
            total += line_total

    return render(request, 'cart/cart_detail.html', {
        'items': items,
        'total': total
    })


def update_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    action = request.POST.get('action')

    if action == "increase":
        item.quantity += 1
        item.save()

    elif action == "decrease":
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()

    return redirect('cart:view_cart')