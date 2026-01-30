from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'category',
            'price',
            'unit_of_measure',
            'stock_quantity',
            'image',
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Organic Tomatoes'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0'}),
        }

        labels = {
            'unit_of_measure': 'Unit (e.g., kg, dozen, bunch)',
            'stock_quantity': 'Quantity Available',
            'image': 'Product Image',
        }
