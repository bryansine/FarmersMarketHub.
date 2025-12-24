from django.test import TestCase


# class FarmerDashboardView(FarmerRequiredMixin, TemplateView):
#     template_name = "users/farmer_dashboard.html"

#     def get_context_data(self, **kwargs):
#         from products.models import Product
#         context = super().get_context_data(**kwargs)

#         farmer = self.request.user
#         products = Product.objects.filter(farmer=farmer).order_by('-created_at')

#         context["products"] = products
#         context["total_products"] = products.count()
#         context["total_stock"] = sum(p.stock_quantity for p in products)
#         context["total_views"] = 0  # placeholder for future
#         return context

