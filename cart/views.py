from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from products.models import Product
from .models import Cart, CartItem
from django.http import JsonResponse

def _get_or_create_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

@login_required
def cart_add(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    qty = int(request.POST.get("quantity", 1))
    if qty < 1:
        qty = 1

    # Prevent adding more than in stock
    if qty > product.stock_quantity:
        qty = product.stock_quantity

    cart = _get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    item.quantity = min(product.stock_quantity, item.quantity + qty)
    item.save()
    return redirect("cart:detail")

@login_required
def cart_update(request, item_pk):
    item = get_object_or_404(CartItem, pk=item_pk, cart__user=request.user)
    qty = int(request.POST.get("quantity", 1))
    if qty <= 0:
        item.delete()
    else:
        # clamp to stock
        item.quantity = min(qty, item.product.stock_quantity)
        item.save()
    return redirect("cart:detail")

@login_required
def cart_remove(request, item_pk):
    item = get_object_or_404(CartItem, pk=item_pk, cart__user=request.user)
    item.delete()
    return redirect("cart:detail")

@login_required
def cart_detail(request):
    cart = _get_or_create_cart(request.user)
    items = cart.items.select_related("product")
    total = cart.total()
    return render(request, "cart/cart_detail.html", {"cart": cart, "items": items, "total": total})
