from django import forms

class CheckoutForm(forms.Form):
    fullname = forms.CharField(max_length=200)
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255, required=False)