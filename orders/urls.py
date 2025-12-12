from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('checkout/item/<int:item_id>/', views.checkout_single_item, name='checkout_single'),
]