import json
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Order, OrderItem
from cart.models import CartItem, Cart
from products.models import Product
from orders.mpesa.stk_push import stk_push
from orders.mpesa.utils import normalize_phone


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/order_detail.html", {"order": order})

def create_order_from_cart(request, form_data):
    if not request.user.is_authenticated:
        return None, "Login required."

    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(cart=cart).select_related("product")

    if not cart_items.exists():
        return None, "Cart is empty."

    total = sum(item.line_total for item in cart_items)

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            full_name=form_data["full_name"],
            phone_number=form_data["phone_number"],
            pickup_address=form_data.get("pickup_address", ""),
            total=total,
            status="pending",
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
                line_total=item.line_total,
            )

        cart_items.delete()

    return order, None


@login_required
def checkout(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone_number")
        pickup_address = request.POST.get("pickup_address", "")

        cart = Cart.objects.filter(user=request.user).first()
        items = CartItem.objects.filter(cart=cart)

        if not items.exists():
            messages.error(request, "Cart is empty.")
            return redirect("cart:view_cart")

        total = sum(i.line_total for i in items)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone,
                pickup_address=pickup_address,
                total=total,
                status="pending",
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity,
                    line_total=item.line_total,
                )

            items.delete()

        callback_url = request.build_absolute_uri(
            reverse("orders:mpesa_callback")
        )

        resp = stk_push(
            amount=total,
            phone=phone,
            account_reference=f"ORDER-{order.id}",
            callback_url=callback_url,
        )

        if resp.get("CheckoutRequestID"):
            order.mpesa_checkout_request_id = resp["CheckoutRequestID"]
            order.mpesa_response = resp
            order.save()
            messages.success(request, "Enter M-Pesa PIN on your phone.")
        else:
            messages.error(request, "Payment initiation failed.")

        return redirect("orders:order_detail", order.id)

    return render(request, "orders/checkout.html")




def checkout_single_item(request, item_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to checkout.")
        return redirect("users:login")

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone_number")
        pickup_address = request.POST.get("pickup_address", "")

        try:
            phone = normalize_phone(phone)
        except ValueError:
            messages.error(request, "Enter a valid Safaricom number.")
            return redirect(request.path)

        line_total = int(cart_item.line_total)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone,
                pickup_address=pickup_address,
                total=line_total,
                status="pending",
            )

            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,
                quantity=cart_item.quantity,
                line_total=line_total,
            )

        callback_url = request.build_absolute_uri(
            reverse("orders:mpesa_callback")
        )

        resp = stk_push(
            amount=line_total,
            phone=phone,
            account_reference=str(order.id),
            callback_url=callback_url,
        )

        if resp.get("CheckoutRequestID"):
            order.mpesa_checkout_request_id = resp["CheckoutRequestID"]
            order.mpesa_response = resp
            order.save()
            cart_item.delete()
            messages.success(request, "M-Pesa prompt sent. Enter your PIN.")
        else:
            order.status = "failed"
            order.mpesa_response = resp
            order.save()
            messages.error(request, "Payment initiation failed.")

        return redirect("orders:order_detail", order.id)

    return render(request, "orders/checkout.html", {
        "single_item": True,
        "item": cart_item,
        "total": cart_item.line_total,
    })

@csrf_exempt
def mpesa_callback(request):
    """
    Receives M-Pesa STK callback from Safaricom
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON"})

    callback = data.get("Body", {}).get("stkCallback", {})
    checkout_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")
    result_desc = callback.get("ResultDesc")

    order = Order.objects.filter(
        mpesa_checkout_request_id=checkout_id
    ).first()

    if not order:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Order not found"})

    order.mpesa_response = callback

    if result_code == 0:
        order.status = "paid"
    else:
        order.status = "failed"

    order.save()

    return JsonResponse({
        "ResultCode": 0,
        "ResultDesc": "Accepted"
    })
