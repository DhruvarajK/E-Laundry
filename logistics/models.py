from django.db import models
from myadmin.models import login
from django.utils import timezone
now = timezone.now()

class DeliveryMan(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    profile_image = models.CharField(max_length=100)
    license_image = models.CharField(max_length=100)
    house = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    post = models.CharField(max_length=100)
    pin = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    LOGIN = models.ForeignKey(login, on_delete=models.CASCADE, default=1)


