
from django.urls import path
from . import views

urlpatterns = [
    path('view_profile_business/', views.view_profile_business, name='view_profile_business'),  # View Profile
    path('profile_update_business/', views.profile_update_business, name='profile_update_business'),
    path('business_register/', views.register_business, name='register_business'),
    path('get-location/', views.get_current_location, name='get_current_location'),
    path('business_home/', views.business_home, name='business_home'),
    path('business_subscription_plans/', views.subscription_plans, name='business_subscription_plans'),
]