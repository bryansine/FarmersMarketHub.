from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart.models import Cart, CartItem
from .models import Order, OrderItem
from .forms import CheckoutForm
from django.db import transaction
from django.urls import reverse
from django.contrib import messages

@login_required
def checkout_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("cart:detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # re-fetch items with select_for_update to lock rows
                cart_items = CartItem.objects.select_related("product").filter(cart=cart)

                # validate stock
                for item in cart_items:
                    if item.quantity > item.product.stock_quantity:
                        messages.error(request, f"Sorry, not enough stock for {item.product.name}.")
                        return redirect("cart:detail")

                total = sum(item.product.price * item.quantity for item in cart_items)

                order = Order.objects.create(
                    user=request.user,
                    fullname=form.cleaned_data["fullname"],
                    phone_number=form.cleaned_data["phone_number"],
                    address=form.cleaned_data.get("address", ""),
                    total=total,
                    status="pending",
                )

                # create order items & decrement stock
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                    # decrement stock
                    item.product.stock_quantity -= item.quantity
                    item.product.save()

                # clear cart
                cart.items.all().delete()

            messages.success(request, "Order placed successfully.")
            return redirect(reverse("orders:success", kwargs={"order_pk": order.pk}))
    else:
        form = CheckoutForm(initial={
            "fullname": request.user.get_full_name() or request.user.username
        })

    total = cart.total() if cart else 0
    return render(request, "orders/checkout.html", {"form": form, "total": total})
