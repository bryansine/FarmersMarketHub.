from django.urls import path
from . import views

app_name = 'daraja'

urlpatterns = [
    path('token/', views.mpesa_token_view, name='mpesa_token'),
]