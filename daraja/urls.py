from . import views
from django.urls import path

app_name = 'daraja'
urlpatterns = [
    path('token/', views.mpesa_token_view, name='mpesa_token'),
]