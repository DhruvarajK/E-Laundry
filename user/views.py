import os
from pyexpat.errors import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import make_aware
from django.conf import settings
from business.models import Business
from .models import LaundryBag, LogisticsAssignment, Machine, Subscription, SubscriptionPlan, user
from geopy.geocoders import Nominatim
from django.core.files.storage import FileSystemStorage
from myadmin.models import login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceOrder, Payment,LaundryBag
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

def user_home(request):
    if request.session['lid'] == 'out':
        return HttpResponse("<script>alert('please login');window.location='/'</script>")
    else:
        try:
            usr_obj = user.objects.get(LOGIN=request.session['lid'])
        except user.DoesNotExist:
             return HttpResponse("<script>alert('User not found');window.location='/'</script>")
        
        active_orders = ServiceOrder.objects.filter(USER=usr_obj).exclude(
            status__in=['completed', 'canceled']
        ).exclude(
            logisticsassignment__delivery_status__in=['delivered', 'Delivered', 'canceled', 'Canceled']
        ).order_by('-order_date')[:3]

        # Fetch recent completed orders
        recent_completed = ServiceOrder.objects.filter(
            USER=usr_obj,
            logisticsassignment__delivery_status__in=['delivered', 'Delivered']
        ).order_by('-order_date')[:5]

        # Fetch quick reorder templates (last 2 unique service types/instructions)
        # We want to show distinct types of past orders
        all_past_orders = ServiceOrder.objects.filter(USER=usr_obj).order_by('-order_date')
        quick_reorder_orders = []
        seen_types = set()
        for o in all_past_orders:
            if o.service_type not in seen_types:
                quick_reorder_orders.append(o)
                seen_types.add(o.service_type)
            if len(quick_reorder_orders) >= 2:
                break

        return render(request, "user_home.html", {
            'user': usr_obj,
            'active_orders': active_orders,
            'recent_completed': recent_completed,
            'quick_reorder_orders': quick_reorder_orders
        })


def quick_reorder(request, order_id):
    if request.session.get('lid') == 'out' or 'lid' not in request.session:
        return redirect('login')
    
    original_order = get_object_or_404(ServiceOrder, id=order_id)
    
    # Check if the order belongs to the user
    usr_obj = user.objects.get(LOGIN=request.session['lid'])
    if original_order.USER != usr_obj:
        messages.error(request, "Invalid order access.")
        return redirect('user_home')

    # Loyalty points check
    if usr_obj.loyalty_points < 0:
        messages.error(request, f'Reorder declined. You have negative loyalty points ({usr_obj.loyalty_points}).')
        return redirect('user_home')

    # Create new order
    new_order = ServiceOrder.objects.create(
        service_for=original_order.service_for,
        USER=original_order.USER,
        BUSINESS=original_order.BUSINESS,
        service_type=original_order.service_type,
        special_instructions=original_order.special_instructions,
        weight=0.0,
        status='pending'
    )

    # Create logistics assignment
    LogisticsAssignment.objects.create(service_order=new_order)

    # Create payment record
    Payment.objects.create(
        service_order=new_order,
        total_price=0.0,
        payment_status='pending'
    )

    messages.success(request, f'Reorder of {new_order.service_type} placed successfully!')
    return redirect('order_confirmed', order_id=new_order.id)


def get_user_context(request):
    """Helper to get user context for the sidebar"""
    context = {}
    if request.session.get('lid') and request.session['lid'] != 'out':
        try:
            usr_obj = user.objects.get(LOGIN=request.session['lid'])
            context['user'] = usr_obj
        except user.DoesNotExist:
            pass
    return context


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


def register_user(request):
    if request.method == "POST":
        # Extracting form data
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        profile_image = request.FILES.get('profile_image')  # Ensure the file is provided
        email = request.POST['email']
        phone_number = request.POST['phone_number']
        num_bags = request.POST['num_bags']
        house = request.POST['house']
        district = request.POST['district']
        place = request.POST['place']
        post = request.POST['post']
        pin = request.POST['pin']
        password1 = request.POST['password']
        latitude = request.POST.get('latitude', None)
        longitude = request.POST.get('longitude', None)

        # Validate file extension
        allowed_extensions = ['jpg', 'jpeg', 'png']
        if profile_image:
            photo_extension = profile_image.name.split('.')[-1].lower()
            if photo_extension not in allowed_extensions:
                messages.error(request, 'Invalid file type! Only JPG, JPEG, and PNG files are allowed.')
                return render(request, 'register_user.html')
            
            # Save file to media folder
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            profile_image_name = f"user_{timestamp}.{photo_extension}"  # Unique file name
            profile_image_path = os.path.join('user', profile_image_name)  # Save in 'media/user/'
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # FileSystemStorage with MEDIA_ROOT
            fs.save(profile_image_path, profile_image)
            pic_url = f"{settings.MEDIA_URL}{profile_image_path}"  # Build URL for accessing the image
        else:
            pic_url = None  # Handle cases where no image is uploaded

        # Check if user already exists
        data = login.objects.filter(username=email)
        if data.exists():
            return HttpResponse("<script>alert('Already exist');window.location='/'</script>")
        
        # Create login entry
        log_obj = login(username=email, password=password1, usertype='user')
        log_obj.save()
        
        # Save user data
        User = user(
            first_name=first_name,
            last_name=last_name,
            profile_image=pic_url,
            email=email,
            phone_number=phone_number,
            num_bags=num_bags,
            house=house,
            district=district,
            place=place,
            post=post,
            pin=pin,
            latitude=latitude if latitude else None,
            LOGIN=log_obj,
            longitude=longitude if longitude else None,
        )
        User.save()

        return HttpResponse("<script>alert('Registered successfully');window.location='/'</script>")
    
    return render(request, 'register_user.html')




@csrf_exempt
def get_current_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
        except json.JSONDecodeError:
            latitude = request.POST.get('latitude', '').strip()
            longitude = request.POST.get('longitude', '').strip()

        if not latitude or not longitude:
            return JsonResponse({'status': 'error', 'message': "Latitude and longitude are missing."}, status=400)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
            location_details = get_location_details(latitude, longitude)

            if location_details:
                return JsonResponse({
                    'status': 'success',
                    'latitude': latitude,
                    'longitude': longitude,
                    'place': location_details['place'],
                    'district': location_details['district'],
                    'state': location_details['state'],
                    'pin': location_details['pin'],
                    'full_address': location_details['full_address'],
                })
            else:
                return JsonResponse({'status': 'error', 'message': "Could not fetch location details."}, status=404)

        except ValueError:
            return JsonResponse({'status': 'error', 'message': "Invalid latitude or longitude values."}, status=400)
    
    return JsonResponse({'status': 'error', 'message': "Only POST requests are allowed."}, status=405)



def view_profile_user(request):
    usr_obj= user.objects.get(LOGIN=request.session['lid'])  # Assuming 'user' is a related field on the User model
    return render(request, 'profile_view_user.html', {'user': usr_obj})

def update_profile_user(request):
    usr_obj= user.objects.get(LOGIN=request.session['lid'])  # Assuming 'user' is a related field on the User model

    if request.method == 'POST':
        # Update fields based on the form input
        usr_obj.first_name = request.POST.get('first_name')
        usr_obj.last_name = request.POST.get('last_name')
        usr_obj.profile_image = request.FILES.get('profile_image') if 'profile_image' in request.FILES else usr_obj.profile_image
        usr_obj.phone_number = request.POST.get('phone_number')
        usr_obj.house = request.POST.get('house')
        usr_obj.district = request.POST.get('district')
        usr_obj.place = request.POST.get('place')
        usr_obj.post = request.POST.get('post')
        usr_obj.pin = request.POST.get('pin')
        usr_obj.save()  # Save the updated data

        return redirect('view_profile_user')  # Redirect to the profile view page after update

    return render(request, 'profile_update_user.html', {'user': usr_obj})

def normal_order(request):
    context = get_user_context(request)
    if request.method == 'POST':
        service_type = request.POST.get('service_type')
        special_instructions = request.POST.get('special_instructions')
        weight = float(request.POST.get('weight', 0))

        # Loyalty points check
        if usr_obj.loyalty_points < 0:
            messages.error(request, f'Order declined. You have negative loyalty points ({usr_obj.loyalty_points}). Please contact support.')
            return render(request, 'normal_order.html', context)

        # Capacity Check Logic
        from django.db.models import Sum
        total_capacity = Machine.objects.filter(is_active=True).aggregate(Sum('capacity'))['capacity__sum'] or 0
        
        today = timezone.now().date()
        existing_weight = ServiceOrder.objects.filter(order_date__date=today).exclude(status='canceled').aggregate(Sum('weight'))['weight__sum'] or 0
        
        if (existing_weight + weight) > total_capacity:
            messages.error(request, f'Order declined. Total machine capacity for today ({total_capacity}kg) is exceeded. Current orders: {existing_weight}kg, Your order: {weight}kg.')
            return render(request, 'normal_order.html', context)

        # Optionally, handle subscription if provided in the form
        subscription_id = request.POST.get('subscription', None)
        subscription_instance = None
        if subscription_id:
            try:
                subscription_instance = Subscription.objects.get(id=subscription_id)
            except Subscription.DoesNotExist:
                subscription_instance = None  # or handle error as needed

        # Get the logged-in user from session
        login_id = request.session['lid']
        login_instance = login.objects.get(id=login_id)

        # Initialize variables for both user and business
        service_for = None
        user_instance = None
        business_instance = None

        # Try to get the user instance; if found, mark service_for as 'user'
        try:
            user_instance = user.objects.get(LOGIN=login_instance)
            service_for = 'user'
        except user.DoesNotExist:
            # If no user is found, try to get the business instance
            try:
                business_instance = Business.objects.get(LOGIN=login_instance)
                service_for = 'business'
            except Business.DoesNotExist:
                # Handle the error (for example, raise an exception or redirect with error message)
                messages.error(request, 'No valid user or business account found.')
                return render(request, 'normal_order.html', context)

        # Create the service order with the appropriate field values
        order = ServiceOrder.objects.create(
            service_for=service_for,
            USER=user_instance,
            BUSINESS=business_instance,
            subscription=subscription_instance,
            service_type=service_type,
            weight=weight,
            special_instructions=special_instructions,
        )

        # Create the logistics assignment if needed
        LogisticsAssignment.objects.create(service_order=order)
        # Create the payment for the order
        payment = Payment.objects.create(
            service_order=order,
            total_price=0
        )
        payment.save()

        messages.success(request, 'Your order have been confirmed!')
        return redirect('order_confirmed', order_id=order.id)

    return render(request, 'normal_order.html', context)


def order_confirmed(request, order_id):
    context = get_user_context(request)
    order = get_object_or_404(ServiceOrder, id=order_id)
    payment = Payment.objects.filter(service_order=order).first()
    
    context.update({'order': order, 'payment': payment})
    return render(request, 'order_confirmed.html', context)







def view_all_orders(request):
    # Grab the login id from the session
    login_id = request.session.get('lid')
    if not login_id:
        # Handle error: maybe redirect to login page or return an error
        return redirect('login')

    try:
        login_instance = login.objects.get(pk=login_id)
    except login.DoesNotExist:
        # Handle error if login instance isn't found
        return redirect('login')

    # Based on the login type, get the corresponding instance and orders
    if login_instance.usertype.lower() == 'user':
        try:
            user_instance = user.objects.get(LOGIN=login_instance)
        except user.DoesNotExist:
            return HttpResponse("User not found", status=404)
        orders = ServiceOrder.objects.filter(USER=user_instance)
    elif login_instance.usertype.lower() == 'business':
        try:
            business_instance = Business.objects.get(LOGIN=login_instance)
        except Business.DoesNotExist:
            return HttpResponse("Business not found", status=404)
        orders = ServiceOrder.objects.filter(BUSINESS=business_instance)
    else:
        # Optionally, handle other types or error out
        return HttpResponse("Invalid user type", status=400)

    # Get the status filter from the request (default is 'all')
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    response = render(request, 'view_all_orders.html', {
        'orders': orders,
        'status_filter': status_filter,  # For dropdown selection in template
    })
    # No caching!
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response



def cancel_order(request, order_id):
    # Fetch the logged-in user or business based on the login type
    login_id = request.session.get('lid')
    if not login_id:
        return redirect('login')

    try:
        login_instance = login.objects.get(pk=login_id)
    except login.DoesNotExist:
        return redirect('login')

    # Determine if the request is from a user or business
    order_filter = {}
    if login_instance.usertype.lower() == 'user':
        try:
            user_instance = user.objects.get(LOGIN=login_instance)
            order_filter = {'USER': user_instance}
        except user.DoesNotExist:
            return HttpResponse("User not found", status=404)
    
    elif login_instance.usertype.lower() == 'business':
        try:
            business_instance = Business.objects.get(LOGIN=login_instance)
            order_filter = {'BUSINESS': business_instance}
        except Business.DoesNotExist:
            return HttpResponse("Business not found", status=404)
    
    else:
        return HttpResponse("Invalid user type", status=400)

    # Fetch the order to cancel
    order = get_object_or_404(ServiceOrder, id=order_id, **order_filter)

    # Check if the order status is 'pending'
    if order.status == 'pending':
        order.status = 'canceled'
        order.save()

        if login_instance.usertype.lower() == 'user':
            user_instance.loyalty_points -= 50
            user_instance.save()

        # Update logistics assignment if it exists
        logistics_assignment = LogisticsAssignment.objects.filter(service_order=order).first()
        if logistics_assignment:
            logistics_assignment.delivery_status = 'canceled'
            logistics_assignment.save()

        # Update payment status if it exists
        payment = Payment.objects.filter(service_order=order).first()
        if payment:
            payment.payment_status = 'refunded' if payment.payment_status == 'paid' else 'canceled'
            payment.save()

        messages.success(request, 'Your order has been canceled successfully. 50 loyalty points have been deducted.')
    else:
        messages.error(request, 'You can only cancel orders that are in the "pending" status.')

    return redirect('view_all_orders')  # Redirect back to the order list



def track_orders(request):
    # Grab the login instance from the session
    login_instance = login.objects.get(id=request.session['lid'])
    
    # Define the valid delivery statuses (both lowercase & title-case)
    valid_statuses = [
        'not_assigned', 'Not Assigned',
        'assigned', 'Assigned', 
        'pickuped', 'Pickuped', 
        'in_transit', 'In Transit', 
        'delivered', 'Delivered'
    ]
    print("All Orders:", ServiceOrder.objects.all())

    
    # Check the type of login to decide whether it's a business or user
    if login_instance.usertype.lower() == 'business':
        # If it's a business login, get the corresponding Business instance
        business_instance = Business.objects.get(LOGIN=login_instance)
        # Assume ServiceOrder has a BUSINESS foreign key field for business orders
        orders = ServiceOrder.objects.filter(
            BUSINESS=business_instance,
            logisticsassignment__delivery_status__in=valid_statuses
        )
        print("Orders After Filter:", orders)

    else:
        # Otherwise, treat it as a user login
        user_instance = user.objects.get(LOGIN=login_instance)
        orders = ServiceOrder.objects.filter(
            USER=user_instance,
            logisticsassignment__delivery_status__in=valid_statuses
        )
        print("Orders After Filter:", orders)

    # Optional date filter from GET parameters (format: YYYY-MM-DD)
    filter_date = request.GET.get('date')
    if filter_date:
        try:
            date_obj = datetime.strptime(filter_date, "%Y-%m-%d").date()
            orders = orders.filter(order_date__date=date_obj)
        except ValueError:
            # If parsing fails, we just skip the date filter – no capsaicin here!
            pass
    
    # Option to hide delivered orders if specified in GET parameters
    hide_delivered = request.GET.get('hide_delivered')
    if hide_delivered:
        orders = orders.exclude(logisticsassignment__delivery_status__in=['delivered', 'Delivered'])
    
    context = {'orders': orders}
    context.update(get_user_context(request))
    return render(request, 'track_orders.html', context)

    
    


# scanner/views.py



def open_scanner(request):
    return render(request, 'qr_scanner.html')



@csrf_exempt  # You can remove this if CSRF token is being passed correctly
def camera(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            if 'image' not in data:
                return JsonResponse({"error": "No image data provided"}, status=400)
            image_data = base64.b64decode(data['image'])
            img = Image.open(io.BytesIO(image_data))
            decoded_objects = decode(img)
            if decoded_objects:
                qr_code = decoded_objects[0].data.decode('utf-8')
                return JsonResponse({"content": qr_code}, status=200)
            else:
                return JsonResponse({"error": "No QR code found"}, status=400)
        return JsonResponse({"error": "Invalid request method"}, status=405)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from django.shortcuts import get_object_or_404
from .models import LaundryBag, ServiceOrder
from django.contrib import messages

def assign_bag_with_qr(request, service_order_id):
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        service_type = request.POST.get('service_type')
        prefer=request.POST.get('prefer')
        service_order = get_object_or_404(ServiceOrder, id=service_order_id)
        user = service_order.USER

        # check if the QR code is already used
        if LaundryBag.objects.filter(qr_code=qr_code).exists():
            messages.error(request, "This QR code is already assigned.")
            return redirect('open_scanner')

        # assign the bag
        LaundryBag.objects.create(
            USER=user,
            bag_number=user.num_bags + 1,
            qr_code=qr_code,
            preference=prefer,
            service_type=service_type
        )
        messages.success(request, "Bag successfully assigned!")
        return redirect('check_assign_bags', service_order_id=service_order.id)




def check_assign_bags(request, service_order_id):
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        service_type = request.POST.get('service_type')
        prefer=request.POST.get('prefer')
        service_order = get_object_or_404(ServiceOrder, id=service_order_id)

        if service_order.service_for == 'business' and service_order.BUSINESS:
            account = service_order.BUSINESS
            current_service = 'business'
        else:
            account = service_order.USER
            current_service = 'user'

        num_bags_needed = account.num_bags

        existing_assigned_bag = LaundryBag.objects.filter(qr_code=qr_code).first()
        if existing_assigned_bag:
            
            assigned_service = 'business' if existing_assigned_bag.BUSINESS else 'user'
            if assigned_service != current_service:
                messages.error(
                    request,
                    "This QR code is already assigned to a different service."
                )
                return HttpResponse(
                "<script>alert('This QR code is already assigned with a different service for your account.');window.location='/assigned-services'</script>"
            )
            else:
                # QR code exists for the same service type, so simply check if the service type matches.
                if existing_assigned_bag.service_type != service_type:
                    messages.error(
                        request,
                        "This QR code is already assigned with a different service for your account."
                    )
                    return HttpResponse(
                "<script>alert('This QR code is already assigned with a different service for your account.');window.location='/assigned-services'</script>"
            )
                else:
                    messages.info(
                        request,
                        "This QR code is already assigned with the same service."
                    )
                return redirect('view_assigned_services')

        if current_service == 'business':
            assigned_bags_count = LaundryBag.objects.filter(BUSINESS=account).count()
        else:
            assigned_bags_count = LaundryBag.objects.filter(USER=account).count()

        if assigned_bags_count >= num_bags_needed:
            messages.error(request, "Cannot assign more bags than the required number.")
            return HttpResponse(
                "<script>alert('Cannot assign more bags than the required number.');window.location='/assigned-services'</script>"
            )

        if current_service == 'business':
            LaundryBag.objects.create(
                BUSINESS=account,
                qr_code=qr_code,
                preference=prefer,
                service_type=service_type
            )
        else:
            LaundryBag.objects.create(
                USER=account,
                qr_code=qr_code,
                preference=prefer,
                service_type=service_type
            )
        messages.success(request, "Laundry bag successfully assigned!")
        return redirect('view_assigned_services')

    return render(request, 'qr_scanner.html', {'service_order_id': service_order_id})



def assign_bags_to_user(user, num_bags):
    for i in range(1, num_bags + 1):
        LaundryBag.objects.create(
            user=user,
            bag_number=i,
            qr_code='',
            service_type=''  
        )

def pickup_laundry(user, bag_service_types):
    bags = LaundryBag.objects.filter(user=user)
    for bag, service_type in zip(bags, bag_service_types):
        bag.service_type = service_type
        bag.assigned = True
        bag.save()




def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    context = {'plans': plans}

    if 'lid' in request.session and request.session['lid'] != 'out':
        try:
            login_instance = login.objects.get(id=request.session['lid'])
            if login_instance.usertype == 'user':
                context.update(get_user_context(request))
                return render(request, 'user_subscription_plans.html', context)
        except login.DoesNotExist:
            pass
            
    return render(request, 'subscription_plans.html', context)



from django.utils.timezone import make_aware
from django.contrib import messages

def subscription_confirmed(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    razorpay_order_id = request.session.get('razorpay_order_id')
    plan_price = subscription.subscription_plan.price
    amount = int(plan_price * 100)
    
    context = {
        'subscription': subscription,
        'order_id': razorpay_order_id,
        'amount': amount,
        'display_amount': plan_price,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    }

    if 'lid' in request.session and request.session['lid'] != 'out':
        try:
            login_instance = login.objects.get(id=request.session['lid'])
            if login_instance.usertype == 'user':
                context.update(get_user_context(request))
                return render(request, 'user_subscription_confirmed.html', context)
        except login.DoesNotExist:
            pass
            
    return render(request, 'subscription_confirmed.html', context)



def subscribe(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
    login_instance = login.objects.get(id=request.session['lid'])

    if login_instance.usertype.lower() == 'business':
        subscription_for = 'business'
        business_instance = Business.objects.get(LOGIN=login_instance)
        active_subscription = Subscription.objects.filter(business=business_instance, is_active=True).exists()
        template_name = 'subscribe.html'
        context = {}
    else:
        subscription_for = 'user'
        user_instance = user.objects.get(LOGIN=login_instance)
        active_subscription = Subscription.objects.filter(user=user_instance, is_active=True).exists()
        template_name = 'user_subscribe.html'
        context = get_user_context(request)

    if active_subscription:
        messages.error(request, "You already have an active subscription. Please wait until it expires before purchasing a new one.")
        context.update({'plan': plan, 'active_subscription': True})
        return render(request, template_name, context)

    if request.method == 'POST':
        try:
            amount = int(plan.price * 100)
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': '1'
            })
            request.session['razorpay_order_id'] = razorpay_order['id']

            now = timezone.now()
            if now.time() > time(10, 0):
                start_date = datetime.combine(now.date() + timedelta(days=1), time(10, 0))
            else:
                start_date = datetime.combine(now.date(), time(10, 0))
            start_date = make_aware(start_date)
            end_date = start_date + timedelta(days=plan.duration_days)

            if subscription_for == 'user':
                subscription = Subscription.objects.create(
                    subscription_for='user',
                    user=user_instance,
                    subscription_plan=plan,
                    end_date=end_date,
                    remaining_services=plan.max_services,
                )
            else:
                subscription = Subscription.objects.create(
                    subscription_for='business',
                    business=business_instance,
                    subscription_plan=plan,
                    end_date=end_date,
                    remaining_services=plan.max_services,
                )

            messages.success(request, 'Subscription successful! Please proceed with payment.')
            return redirect('subscription_confirmed', subscription_id=subscription.id)
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            context.update({'plan': plan, 'active_subscription': False})
            return render(request, template_name, context)

    context.update({'plan': plan, 'active_subscription': False})
    return render(request, template_name, context)


from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render
from .models import Subscription, Business, user, login  

def subscription_details(request):
    login_instance = login.objects.get(id=request.session['lid'])
    
    template_name = 'subscription_details.html'
    context = {}

    if login_instance.usertype.lower() == 'business':
        business_instance = Business.objects.get(LOGIN=login_instance)
        subscription = Subscription.objects.filter(business=business_instance, is_active=True).first()
    else:
        user_instance = user.objects.get(LOGIN=login_instance)
        subscription = Subscription.objects.filter(user=user_instance, is_active=True).first()
        template_name = 'user_subscription_details.html'
        context = get_user_context(request)

    if subscription:
        now = timezone.now()
        if subscription.end_date > now:
            days_remaining = (subscription.end_date - now).days
        else:
            days_remaining = 0
            subscription.is_active = False  
        subscription.remaining_services = days_remaining
        subscription.save()
    else:
        days_remaining = 0

    context.update({
        'subscription': subscription,
        'days_remaining': days_remaining,
    })
    return render(request, template_name, context)




def terms_and_conditions(request):
    return render(request, 'terms_and_conditions.html')

def about_us(request):
    return render(request, 'about_us.html')

def dry_cleaning(request):
    return render(request, 'dry_cleaning.html')

def express_wash(request):
    return render(request, 'express_wash.html')

def ironing(request):
    return render(request, 'ironing.html')

def network(request):
    return render(request, 'network.html')

def careers(request):
    return render(request, 'careers.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    return render(request, 'terms_of_service.html')



def scan_qr_page(request):
    return render(request, 'scan_qr.html')

@csrf_exempt
def process_camera(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            if 'image' not in data:
                return JsonResponse({"error": "No image data provided"}, status=400)
            image_data = base64.b64decode(data['image'])
            img = Image.open(io.BytesIO(image_data))
            decoded_objects = decode(img)
            if decoded_objects:
                qr_code = decoded_objects[0].data.decode('utf-8')
                return JsonResponse({"content": qr_code}, status=200)
            else:
                return JsonResponse({"error": "No QR code found"}, status=400)
        return JsonResponse({"error": "Invalid request method"}, status=405)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def bag_details(request):
    qr_code = request.GET.get('qr_code')
    if qr_code:
        try:
            bag = LaundryBag.objects.get(qr_code=qr_code)
            return render(request, 'bag_details.html', {'bag': bag})
        except LaundryBag.DoesNotExist:
            return render(request, 'bag_details.html', {'error': "No details found for this QR code."})
    else:
        return redirect('scan_qr_page')
    





def razorpay_payment(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    payment = order.payment


    amount_in_paise = int(payment.total_price * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    razorpay_order = client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"order_rcptid_{order.id}",
        "payment_capture": 1,  
    })

    context = {
        "order": order,
        "total_price": amount_in_paise,
        "amount_display": payment.total_price,
        "razorpay_order_id": razorpay_order['id'],  # razorpay order ID
        "razorpay_key": settings.RAZORPAY_KEY_ID
    }
    return render(request, "razorpay_payment.html", context)

def payment_success(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    payment = order.payment
    if payment.payment_status != 'paid':
        payment.payment_status = 'paid'
        payment.save()

    return redirect('view_all_orders')
