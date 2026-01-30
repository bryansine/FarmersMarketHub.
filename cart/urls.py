from . import views
from django.urls import path

app_name = 'cart'

urlpatterns = [
    path('', views.view_cart, name='view_cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove'),
    path("update/<int:item_id>/", views.update_quantity, name="update"),
]