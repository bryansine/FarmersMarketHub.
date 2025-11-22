from django.contrib import admin
from django.urls import path, include
from products.views import product_list
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page → product_list
    path("", product_list, name="home"),

    # Users app
    path("users/", include("users.urls", namespace="users")),

    # Products app
    path("products/", include("products.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
