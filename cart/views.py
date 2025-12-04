from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import CartItem
from django.http import JsonResponse

def _get_session_cart(request):
    """Return dict mapping product_id -> qty stored in session"""
    return request.session.setdefault('cart', {})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    qty = int(request.POST.get('quantity', 1))

    if request.user.is_authenticated:
        obj, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            obj.quantity += qty
        else:
            obj.quantity = qty
        obj.save()
    else:
        cart = _get_session_cart(request)
        cart[str(product_id)] = cart.get(str(product_id), 0) + qty
        request.session.modified = True

    # if request.is_ajax():
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('products:list')

def remove_from_cart(request, product_id):
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user, product_id=product_id).delete()
    else:
        cart = _get_session_cart(request)
        cart.pop(str(product_id), None)
        request.session.modified = True
    return redirect('cart:view_cart')

def view_cart(request):
    items = []
    total = 0
    if request.user.is_authenticated:
        qs = CartItem.objects.filter(user=request.user).select_related('product')
        for ci in qs:
            items.append({'product': ci.product, 'quantity': ci.quantity, 'line_total': ci.line_total})
            total += float(ci.line_total)
    else:
        cart = _get_session_cart(request)
        ids = [int(pid) for pid in cart.keys()]
        products = Product.objects.filter(id__in=ids)
        prod_map = {p.id: p for p in products}
        for pid, qty in cart.items():
            p = prod_map.get(int(pid))
            if not p: continue
            line = qty * float(p.price)
            items.append({'product': p, 'quantity': qty, 'line_total': line})
            total += line

    return render(request, 'cart/cart_detail.html', {'items': items, 'total': total})
