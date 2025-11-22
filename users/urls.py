from django.urls import path
from .views import (
    RegisterView,
    CustomLoginView,
    CustomLogoutView,
    ProfileUpdateView,
    FarmerDashboardView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("dashboard/farmer/", FarmerDashboardView.as_view(), name="farmer_dashboard"),
]