# from django.urls import path
# from . import views

# app_name = "orders"

# urlpatterns = [
#     path("checkout/", views.checkout, name="checkout"),
#     path("checkout/item/<int:item_id>/", views.checkout_single_item, name="checkout_single"),
#     path("order/<int:pk>/", views.order_detail, name="order_detail"),
# ]

from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/item/<int:item_id>/", views.checkout_single_item, name="checkout_single"),
    path("order/<int:pk>/", views.order_detail, name="order_detail"),
    path('initiate-payment/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/waiting/<int:order_id>/', views.payment_waiting, name='payment_waiting'),
    path('payment/status/<int:order_id>/', views.check_payment_status, name='check_payment_status'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
]