from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

# Import the necessary components from the products app
from .models import Product
from .forms import ProductForm

# Import the FarmerRequiredMixin from the users app
# Assuming FarmerRequiredMixin is defined in users/views.py
from users.views import FarmerRequiredMixin


# --- Public/Marketplace Views (Function-based views defined earlier) ---

def product_list(request):
    """
    Displays a list of all available products (the main marketplace page).
    """
    # Use Product.objects.select_related('category', 'farmer') for better performance
    products = Product.objects.all().filter(stock_quantity__gt=0).order_by('name')
    context = {'products': products}
    return render(request, 'products/product_list.html', context)

def product_detail(request, pk):
    """
    Displays the detail page for a single product.
    """
    product = get_object_or_404(Product, pk=pk)
    context = {'product': product}
    return render(request, 'products/product_detail.html', context)


# --- Farmer Management Views (Class-based views) ---

class ProductCreateView(FarmerRequiredMixin, CreateView):
    """
    Allows a farmer to create a new product listing.
    Requires user to be logged in and be a farmer.
    """
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('users:farmer_dashboard') # Redirect back to dashboard on success

    def form_valid(self, form):
        # Automatically set the 'farmer' field to the currently logged-in user
        form.instance.farmer = self.request.user
        return super().form_valid(form)


class ProductUpdateView(FarmerRequiredMixin, UpdateView):
    """
    Allows a farmer to update their existing product listing.
    Requires user to be logged in and be the owner of the product.
    """
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('users:farmer_dashboard')

    def get_queryset(self):
        """Ensures a farmer can only edit their own products."""
        queryset = super().get_queryset()
        # Filter the queryset to only include products owned by the current user
        return queryset.filter(farmer=self.request.user)


class ProductDeleteView(FarmerRequiredMixin, DeleteView):
    """
    Allows a farmer to delete their product listing.
    Requires user to be logged in and be the owner of the product.
    """
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('users:farmer_dashboard')

    def get_queryset(self):
        """Ensures a farmer can only delete their own products."""
        queryset = super().get_queryset()
        # Filter the queryset to only include products owned by the current user
        return queryset.filter(farmer=self.request.user)