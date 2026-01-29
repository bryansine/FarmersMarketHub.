import json
import requests
from django.db import transaction
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from daraja.utils import MpesaClient, format_phone_number

from .models import Order, OrderItem
from cart.models import CartItem, Cart
# from daraja.utils import get_mpesa_access_token, generate_password, get_timestamp

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})

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
                total=total,
                status="pending",
                pickup_address=pickup_address
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

        # After creating order, we redirect to initiate payment immediately
        return redirect('orders:initiate_payment', order_id=order.id)

    return render(request, "orders/checkout.html")

@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Initialize the client
    client = MpesaClient()
    
    # Trigger the push using the class method
    response = client.stk_push(
        phone_number=order.phone_number,
        amount=order.total,
        account_reference=f"ORD{order.id}",
        callback_url=settings.MPESA_CALLBACK_URL
    )

    if response.get("ResponseCode") == "0":
        order.mpesa_checkout_request_id = response["CheckoutRequestID"]
        order.save()
        return redirect('orders:payment_waiting', order_id=order.id)
    else:
        messages.error(request, f"Payment failed: {response.get('CustomerMessage', 'Try again')}")
        return redirect('orders:order_detail', pk=order.id)
def payment_waiting(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/payment_waiting.html', {'order': order})

def check_payment_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Match the status in your Farmers Hub Order model ('paid')
    if order.status == "paid":
        return JsonResponse({"status": "success"})
    elif order.status == "failed":
        return JsonResponse({"status": "failed"})
    else:
        return JsonResponse({"status": "pending"})

@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body)
    stk_callback = data.get("Body", {}).get("stkCallback", {})
    checkout_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    order = Order.objects.filter(mpesa_checkout_request_id=checkout_id).first()
    if order:
        if result_code == 0:
            order.status = "paid"
        else:
            order.status = "failed"
        order.save()
    
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@login_required
def checkout_single_item(request, item_id):
    # Standard logic to create order for one item, then redirect to initiate_payment
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone_number=request.POST.get("phone_number"),
                total=cart_item.line_total,
                status="pending"
            )
            OrderItem.objects.create(
                order=order, product=cart_item.product, 
                price=cart_item.product.price, quantity=cart_item.quantity, 
                line_total=cart_item.line_total
            )
            cart_item.delete()
        return redirect('orders:initiate_payment', order_id=order.id)
    return render(request, "orders/checkout.html", {"item": cart_item})

@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Double check if it's paid, otherwise the user might just be guessing URLs
    if order.status != 'paid':
        return redirect('orders:order_detail', pk=order.id)
        
    return render(request, 'orders/payment_success.html', {'order': order})

@login_required
def payment_failed(request):
    return render(request, 'orders/payment_failed.html')