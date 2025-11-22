from .models import Product
from .forms import ProductForm
from django.urls import reverse_lazy
from users.views import FarmerRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

def product_list(request):
    """
    Displays a list of all available products (the main marketplace page).
    """
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


class ProductCreateView(FarmerRequiredMixin, CreateView):
    """
    Allows a farmer to create a new product listing.
    Requires user to be logged in and be a farmer.
    """
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('users:farmer_dashboard')

    def form_valid(self, form):
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
        return queryset.filter(farmer=self.request.user)