import json
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order, OrderItem
from cart.models import CartItem, Cart
from products.models import Product
# from .mpesa import stk_push
# from .mpesa.stk_push import stk_push
from orders.mpesa.stk_push import stk_push

from django.shortcuts import render, redirect, get_object_or_404

# from .mpesa.utils import normalize_phone

from orders.mpesa.stk_push import stk_push



import json
import logging
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import Order
# from orders.mpesa.utils import (
#     get_mpesa_access_token,
#     generate_password,
#     get_timestamp,
# )

logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_status not in ["Pending", "Failed"]:
        messages.error(request, "Payment already processed.")
        return redirect("orders:order_detail", order_id=order.id)

    access_token = get_mpesa_access_token()
    if not access_token:
        messages.error(request, "Failed to get M-Pesa access token.")
        return redirect("orders:order_detail", order_id=order.id)

    timestamp = get_timestamp()
    password = generate_password()

    phone_number = str(order.phone_number).strip()
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(order.total_price),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": f"ORDER-{order.id}",
        "TransactionDesc": f"Payment for Order {order.id}",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    response = requests.post(
        stk_url,
        headers=headers,
        data=json.dumps(payload),
        timeout=30,
    )

    logger.warning("STK STATUS: %s", response.status_code)
    logger.warning("STK BODY: %s", response.text)

    response_data = response.json()

    if response.status_code == 200 and response_data.get("ResponseCode") == "0":
        order.mpesa_checkout_id = response_data["CheckoutRequestID"]
        order.payment_status = "Payment Initiated"
        order.save()
        return redirect("orders:payment_waiting", order_id=order.id)

    messages.error(
        request,
        response_data.get("errorMessage", "Payment initiation failed."),
    )
    order.payment_status = "Failed"
    order.save()

    return redirect("orders:order_detail", order_id=order.id)


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})


def create_order_from_cart(request, form_data):

    if request.user.is_authenticated:
        user_cart = Cart.objects.filter(user=request.user).first()
        cart_qs = CartItem.objects.filter(cart=user_cart).select_related('product')
        if not cart_qs.exists():
            return None, "Cart is empty."

        total = sum(ci.line_total for ci in cart_qs)

    else:
        cart = request.session.get('cart', {})
        if not cart:
            return None, "Cart is empty."

        ids = [int(i) for i in cart.keys()]
        products = Product.objects.filter(id__in=ids)
        total = sum(products.get(id=int(pid)).price * qty for pid, qty in cart.items())

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=form_data['full_name'],
            phone_number=form_data['phone_number'],
            pickup_address=form_data.get('pickup_address', ''),
            total=total,
        )

        if request.user.is_authenticated:
            for ci in cart_qs:
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    price=ci.product.price,
                    quantity=ci.quantity,
                    line_total=ci.line_total,
                )
            cart_qs.delete()

        else:
            cart = request.session.get('cart', {})
            for pid, qty in cart.items():
                prod = Product.objects.get(pk=int(pid))
                line_total = prod.price * qty
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    price=prod.price,
                    quantity=qty,
                    line_total=line_total,
                )
            request.session['cart'] = {}
            request.session.modified = True

    return order, None


def checkout(request):
    if request.method == 'POST':
        form_data = {
            'full_name': request.POST.get('full_name'),
            'phone_number': request.POST.get('phone_number'),
            'pickup_address': request.POST.get('pickup_address', ''),
        }

        order, err = create_order_from_cart(request, form_data)
        if err:
            messages.error(request, err)
            return redirect('cart:view_cart')

        callback_url = request.build_absolute_uri(reverse('orders:mpesa_callback'))

        resp = stk_push(
            amount=float(order.total),
            phone=form_data['phone_number'],
            account_reference=str(order.id),
            callback_url=callback_url,
        )

        if resp.get('CheckoutRequestID'):
            order.mpesa_checkout_request_id = resp['CheckoutRequestID']
            order.mpesa_response = resp
            order.save()
            messages.info(request, 'M-Pesa STK sent. Enter PIN on your phone.')
        else:
            messages.error(request, 'Payment initiation failed.')

        return redirect('orders:order_detail', order.id)

    return render(request, 'orders/checkout.html')



def checkout_single_item(request, item_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to checkout.")
        return redirect("users:login")

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user
    )

    line_total = int(cart_item.line_total)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        raw_phone = request.POST.get('phone_number')
        pickup_address = request.POST.get('pickup_address', '')

        try:
            phone_number = normalize_phone(raw_phone)
        except ValueError:
            messages.error(request, "Enter a valid Safaricom phone number.")
            return redirect(request.path)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=full_name,
                phone_number=phone_number,
                pickup_address=pickup_address,
                total=line_total,
                status='pending',
            )

            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.product.price,
                quantity=cart_item.quantity,
                line_total=line_total,
            )

        callback_url = request.build_absolute_uri(
            reverse('orders:mpesa_callback')
        )

        resp = stk_push(
            amount=line_total,
            phone=phone_number,
            account_reference=f"ORDER-{order.id}",
            callback_url=callback_url,
        )

        print("MPESA RESPONSE:", resp)

        if resp and resp.get('CheckoutRequestID'):
            order.mpesa_checkout_request_id = resp['CheckoutRequestID']
            order.mpesa_response = resp
            order.save()

            cart_item.delete()

            messages.success(
                request,
                "M-Pesa prompt sent. Enter your PIN."
            )
        else:
            order.status = 'failed'
            order.mpesa_response = resp
            order.save()

            messages.error(
                request,
                "Payment could not be initiated."
            )

        return redirect('orders:order_detail', order.id)

    return render(request, 'orders/checkout.html', {
        'single_item': True,
        'item': cart_item,
        'total': line_total,
    })


@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body.decode("utf-8"))

    callback = data.get("Body", {}).get("stkCallback", {})
    checkout_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")

    order = Order.objects.filter(
        mpesa_checkout_request_id=checkout_id
    ).first()

    if not order:
        return JsonResponse({"ResultCode": 1})

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
