import os
from pyexpat.errors import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from business.models import Business
from geopy.geocoders import Nominatim
from django.conf import settings
from geopy.geocoders import Nominatim
from django.core.files.storage import FileSystemStorage
from myadmin.models import login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
import base64
from pyzbar.pyzbar import decode
from PIL import Image
import io
from django.http import JsonResponse
import json
from datetime import datetime, time, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import razorpay  

from user.models import SubscriptionPlan

def business_home(request):
    if request.session['lid'] == 'out':
        return HttpResponse("<script>alert('please login');window.location='/'</script>")
    else:
        return render(request,"business_home.html")


def get_location_address(lat, lon):
    geolocator = Nominatim(user_agent="your_app_name")
    location = geolocator.reverse((lat, lon), language='en')
    return location.address if location else "Location not found."



def get_location_details(lat, lon):
    geolocator = Nominatim(user_agent="your_app_name")
    location = geolocator.reverse((lat, lon), language='en')
    
    if location:
        address = location.raw.get('address', {})
        return {
            'place': address.get('village') or address.get('town') or address.get('city') or address.get('hamlet'),
            'district': address.get('state_district'),
            'state': address.get('state'),
            'pin': address.get('postcode'),
            'country': address.get('country'),
            'full_address': location.address,
        }
    return None

def register_business(request):
    if request.method == "POST":
        # Extracting form data for the business
        business_name = request.POST['business_name']
        owner_name = request.POST['owner_name']
        business_email = request.POST['business_email']
        business_phone_number = request.POST['business_phone_number']
        business_address = request.POST['business_address']
        district = request.POST['district']
        place = request.POST['place']
        post = request.POST['post']
        pin = request.POST['pin']
        business_type = request.POST['business_type']
        registration_number = request.POST['registration_number']
        num_bags = request.POST['num_bags']
        password = request.POST['password']
        latitude = request.POST.get('latitude', None)
        longitude = request.POST.get('longitude', None)

        # Check if business already exists by verifying login credentials
        data = login.objects.filter(username=business_email)
        if data.exists():
            return HttpResponse("<script>alert('Already exist');window.location='/'</script>")

        # Create a login entry for the business user
        log_obj = login(username=business_email, password=password, usertype='business')
        log_obj.save()

        # Save the business data
        new_business = Business(
            business_name=business_name,
            owner_name=owner_name,
            business_email=business_email,
            business_phone_number=business_phone_number,
            business_address=business_address,
            district=district,
            place=place,
            post=post,
            pin=pin,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            business_type=business_type,
            num_bags=num_bags,
            LOGIN=log_obj,
            registration_number=registration_number
        )
        new_business.save()

        return HttpResponse("<script>alert('Registered successfully');window.location='/'</script>")
    
    return render(request, 'register_business.html')

def view_profile_business(request):
    usr_obj= Business.objects.get(LOGIN=request.session['lid'])  # Assuming 'user' is a related field on the User model
    return render(request, 'profile_view_business.html', {'user': usr_obj})

def profile_update_business(request):
    usr_obj= Business.objects.get(LOGIN=request.session['lid'])  # Assuming 'user' is a related field on the User model

    if request.method == 'POST':
        # Update fields based on the form input
        usr_obj.business_name = request.POST.get('business_name')
        usr_obj.owner_name = request.POST.get('owner_name')
        usr_obj.business_phone_number = request.POST.get('business_phone_number')
        usr_obj.business_address = request.POST.get('business_address')
        usr_obj.district = request.POST.get('district')
        usr_obj.place = request.POST.get('place')
        usr_obj.post = request.POST.get('post')
        usr_obj.pin = request.POST.get('pin')
        usr_obj.save()  # Save the updated data

        return redirect('view_profile_business')  # Redirect to the profile view page after update

    return render(request, 'profile_update_business.html', {'user': usr_obj})




@csrf_exempt
def get_current_location(request):
    if request.method == "POST":
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()

        # Check if latitude and longitude are provided
        if not latitude or not longitude:
            return render(request, 'current_location.html', {
                'error': "Latitude and longitude are missing. Please allow location access and try again."
            })

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            location_details = get_location_details(latitude, longitude)

            if location_details:
                return render(request, 'register_business.html', {
                    'latitude': latitude,
                    'longitude': longitude,
                    'place': location_details['place'],
                    'district': location_details['district'],
                    'state': location_details['state'],
                    'pin': location_details['pin'],
                    'full_address': location_details['full_address'],
                })
            else:
                return render(request, 'current_location.html', {
                    'error': "Could not fetch location details. Please try again."
                })

        except ValueError:
            return render(request, 'current_location.html', {
                'error': "Invalid latitude or longitude values."
            })
    return render(request, 'current_location.html')


def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'subscription_plans.html', {'plans': plans})


