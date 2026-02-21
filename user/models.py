from datetime import timedelta
from django.db import models
from business.models import Business
from logistics.models import DeliveryMan
from myadmin.models import login
from django.utils import timezone
from django.core.exceptions import ValidationError

now = timezone.now()



class user(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_image = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    house = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    post = models.CharField(max_length=100)
    pin = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    num_bags = models.PositiveIntegerField(default=1)
    LOGIN = models.ForeignKey(login, on_delete=models.CASCADE, default=1)
    


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)  # weekly or monthly
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price for the plan
    duration_days = models.PositiveIntegerField()  # Number of days the subscription is valid
    service_type = models.CharField(max_length=100, null=True, blank=True)  # e.g., "hand wash", "machine wash"
    max_services = models.PositiveIntegerField()  # Maximum services allowed in the plan
    description = models.TextField(null=True, blank=True)  # Plan details

    def __str__(self):
        return self.name



class Subscription(models.Model):
    SUBSCRIPTION_FOR_CHOICES = [
        ('user', 'User'),
        ('business', 'Business'),
    ]

    subscription_for = models.CharField(max_length=10, choices=SUBSCRIPTION_FOR_CHOICES)
    user = models.ForeignKey(user, on_delete=models.CASCADE, null=True, blank=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, null=True, blank=True)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    remaining_services = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        if self.subscription_for == 'user':
            return f"User: {self.user.username} - {self.subscription_plan.name}"
        return f"Business: {self.business.name} - {self.subscription_plan.name}"




class LaundryBag(models.Model):
    USER = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    BUSINESS = models.ForeignKey(Business, on_delete=models.CASCADE,null=True,blank=True)
    qr_code = models.CharField(max_length=100, null=True, blank=True)
    service_type = models.CharField(max_length=100, null=True, blank=True)  # e.g., "hand wash", "machine wash"
    preference = models.CharField(max_length=100, null=True, blank=True)  # e.g., "hand wash", "machine wash"
    assigned = models.BooleanField(default=True)


class Machine(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.FloatField(help_text="Capacity in kg")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.capacity}kg)"


# Updated ServiceOrder Model to Handle Subscription
class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('pickup_assigned', 'Pickup Assigned'),
        ('in_progress', 'in progress'),
        ('Washing', 'washing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    SERVICE_FOR_CHOICES = [
        ('user', 'User'),
        ('business', 'Business'),
    ]

    service_for = models.CharField(max_length=10, choices=SERVICE_FOR_CHOICES,  null=True, blank=True)
    USER = models.ForeignKey(user, on_delete=models.CASCADE,null=True, blank=True)
    BUSINESS = models.ForeignKey(Business, on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.CharField(max_length=100)  # e.g., Wash, Iron, Dry Clean
    order_date = models.DateTimeField(auto_now_add=True)
    pickup_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    weight = models.FloatField(default=0.0, help_text="Weight of laundry in kg")
    special_instructions = models.TextField(null=True, blank=True)
    
    

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('processing', 'Processing'),
        ('canceled', 'Canceled'),
    ]

    service_order = models.OneToOneField(ServiceOrder, on_delete=models.CASCADE, related_name="payment")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)  # Total cost calculated
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
    )
    created_at = models.DateTimeField(auto_now_add=True)


    def generate_bill(self):
            bill_details = f"--- Laundry Bill ---\n"
            bill_details += f"Order ID: {self.service_order.id}\n"
            bill_details += f"Date: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            bill_details += "Bill Items:\n"
            total_price = 0
            for item in self.bill_items.all():
                item_total = item.total_price
                bill_details += f"- {item.item_type.capitalize()}: {item.quantity} x ${item.price_per_item} = ${item_total}\n"
                total_price += item_total

            bill_details += f"\nTotal Price: ${total_price}\n"
            bill_details += f"Payment Status: {self.get_payment_status_display()}\n"
            bill_details += "----------------------\n"
            bill_details += "Thank you for using our service!\n"
            return bill_details


class BillItem(models.Model):
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name="bill_items")
    item_type = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.price_per_item

    def __str__(self):
        return f"{self.item_type} ({self.quantity} x {self.price_per_item})"
    

class LogisticsAssignment(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('not_assigned', 'Not Assigned'),
        ('assigned', 'Assigned'),
        ('pickuped', 'Pickuped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled'),
    ]

    service_order = models.OneToOneField(ServiceOrder, on_delete=models.CASCADE)
    pickup_or_delivery_man = models.ForeignKey(DeliveryMan, related_name='pickup_orders', on_delete=models.SET_NULL, null=True, blank=True)  # For pickup tasks
    assignment_date = models.DateTimeField(auto_now_add=True)
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='Not Assigned')

    def __str__(self):
        return f"Logistics for Order #{self.service_order.id}"
    
    