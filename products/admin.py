from django.contrib import admin
from .models import ProductCategory, Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'farmer', 
        'category', 
        'price', 
        'stock_quantity', 
        'unit_of_measure',
        'pickup_address',
        'created_at'
    )
    list_filter = ('category', 'unit_of_measure', 'created_at')
    search_fields = ('name', 'description', 'farmer__username', 'pickup_address')
    # Use raw_id_fields for large ForeignKey fields if needed, but not necessary yet.


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}