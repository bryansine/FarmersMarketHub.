from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductCategory(models.Model):
    """
    Model for different categories of products (e.g., 'Vegetables', 'Fruits').
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, help_text="A short label for URLs.")

    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ('name',)

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    GeoDjango fields are excluded to skip system dependency issues for now.
    """
    farmer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='products_listed',
        limit_choices_to={'is_farmer': True}
    )
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True
    )
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='product_images/', 
        blank=True, 
        null=True
    )

    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Price per unit (e.g., KES 50.00)"
    )
    unit_of_measure = models.CharField(
        max_length=50, 
        default='Kg', 
        help_text="e.g., Kg, sack, crate, dozen"
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    
    # Placeholder for Location 
    pickup_address = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="The physical location for pickup."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return f"{self.name} by {self.farmer.username}"