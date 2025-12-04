# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Order, OrderItem
from cart.models import CartItem
from products.models import Product
from .mpesa import stk_push


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})


def create_order_from_cart(request, form_data):
    if request.user.is_authenticated:
        cart_qs = CartItem.objects.filter(user=request.user).select_related('product')
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
            products = Product.objects.filter(id__in=[int(i) for i in cart.keys()])
            for pid, qty in cart.items():
                prod = Product.objects.get(pk=int(pid))
                line = prod.price * qty
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    price=prod.price,
                    quantity=qty,
                    line_total=line,
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


@csrf_exempt
def mpesa_callback(request):
    data = json.loads(request.body.decode('utf-8'))
    callback = data.get('Body', {}).get('stkCallback', {})

    checkout_id = callback.get('CheckoutRequestID')
    result_code = callback.get('ResultCode')

    order = Order.objects.filter(mpesa_checkout_request_id=checkout_id).first()
    if not order:
        return JsonResponse({"ResultCode": 1})

    order.mpesa_response = callback
    if result_code == 0:
        order.status = 'paid'
    else:
        order.status = 'failed'
    order.save()

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
