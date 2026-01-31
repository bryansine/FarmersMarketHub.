from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_farmer = models.BooleanField(
        default=False,
        help_text='Designates whether this user should be treated as a farmer (seller).'
    )

    is_customer = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as a customer (buyer).'
    )

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.email if self.email else self.username
