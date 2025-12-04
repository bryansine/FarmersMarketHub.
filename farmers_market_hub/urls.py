from django.contrib import admin
from django.urls import path, include
from products.views import product_list
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", product_list, name="home"),
    path("users/", include("users.urls", namespace="users")),
    path("products/", include("products.urls")),
    # path('cart/', include('cart.urls', namespace='cart')),
    # path('orders/', include('orders.urls', namespace='orders')),  
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls'))  
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    