from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User Model for the Farmers Market Hub.
    Includes role differentiation via the 'is_farmer' and 'is_customer' fields.
    """
    is_farmer = models.BooleanField(
        default=False,
        help_text='Designates whether this user should be treated as a farmer (seller).'
    )

    # Keep a customer flag so roles are explicit and safe to reference
    is_customer = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as a customer (buyer).'
    )

    # Contact
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.email if self.email else self.username
