from .models import User
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import UserRegisterForm, UserLoginForm
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class FarmerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restricts access to users who are authenticated AND have is_farmer=True.
    """
    login_url = reverse_lazy('users:login')

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_farmer

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.warning(self.request, "You must be a farmer to access that page.")
            return redirect('products:list')
        return super().handle_no_permission()



class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        messages.success(self.request, "Your account has been created. You can now log in.")
        return super().form_valid(form)


class CustomLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = "users/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_farmer:
            return reverse_lazy("users:farmer_dashboard")
        return reverse_lazy("products:list")



class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("products:list")



class FarmerDashboardView(FarmerRequiredMixin, TemplateView):
    template_name = "users/farmer_dashboard.html"

    def get_context_data(self, **kwargs):
        from products.models import Product
        context = super().get_context_data(**kwargs)

        farmer = self.request.user
        products = Product.objects.filter(farmer=farmer).order_by('-created_at')

        context["products"] = products
        context["total_products"] = products.count()
        context["total_stock"] = sum(p.stock_quantity for p in products)
        context["total_views"] = 0  # placeholder until you add the views field
        return context



class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["username", "email", "phone_number"]
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated.")
        return super().form_valid(form)
