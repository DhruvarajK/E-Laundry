from datetime import timedelta
from django.db import models

from myadmin.models import login

class Business(models.Model):
    business_name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    business_email = models.EmailField(unique=True, max_length=254)
    business_phone_number = models.CharField(max_length=15)
    business_address = models.CharField(max_length=200)
    district = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    post = models.CharField(max_length=100)
    pin = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    business_type = models.CharField(max_length=50)
    num_bags = models.PositiveIntegerField(default=1)
    registration_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    LOGIN = models.ForeignKey(login, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.business_name
    

