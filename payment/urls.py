
from django.urls import path
from . import views

urlpatterns = [
    path('payment-history/', views.payment_history, name='payment_history'),
]