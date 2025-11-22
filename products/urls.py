from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('<int:pk>/', views.product_detail, name='detail'),

     # 🌟 Farmer CRUD Views (Requires Farmer Login)
    # Accessible via /create/, /<pk>/edit/, /<pk>/delete/
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
]