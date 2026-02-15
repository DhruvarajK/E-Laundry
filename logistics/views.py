import base64
import io
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from .models import DeliveryMan
from myadmin.models import login
from django.conf import settings
import os
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
import base64
from pyzbar.pyzbar import decode
from PIL import Image
from django.shortcuts import get_object_or_404,redirect
from user.models import LaundryBag, Payment, ServiceOrder
from django.contrib import messages
from datetime import datetime
from myadmin.views import send_email


def get_dashboard_stats(delivery_man):
    # Completed Assignments
    completed_assignments = LogisticsAssignment.objects.filter(
        pickup_or_delivery_man=delivery_man,
        delivery_status='delivered'
    )
    completed_count = completed_assignments.count()
    
    # Earnings Calculation
    earnings = 0
    for assignment in completed_assignments:
        try:
            # Check if payment exists and is paid
            if hasattr(assignment.service_order, 'payment') and assignment.service_order.payment.payment_status == 'paid':
                 if assignment.service_order.payment.total_price:
                    earnings += assignment.service_order.payment.total_price
        except Exception:
            pass
            
    # Pending / Active Assignments (Assigned, Picked Up, In Transit)
    pending_assignments = LogisticsAssignment.objects.filter(
        pickup_or_delivery_man=delivery_man,
        delivery_status__in=['assigned', 'pickuped', 'in_transit']
    )
    pending_count = pending_assignments.count()

    # Assessments/Jobs Assigned Today
    try:
        today = timezone.now().date()
        today_assignments = LogisticsAssignment.objects.filter(
            pickup_or_delivery_man=delivery_man,
            assignment_date__date=today
        )
        today_count = today_assignments.count()
    except Exception:
        today_count = 0

    return {
        'completed_count': completed_count,
        'earnings': earnings,
        'pending_count': pending_count,
        'today_count': today_count
    }

def logistics_home(request):
    login_id = request.session.get('lid')
    if not login_id or login_id == 'out':
        return HttpResponse("<script>alert('please login');window.location='/'</script>")
    
    try:
        delivery_man = DeliveryMan.objects.get(LOGIN__id=login_id)
        stats = get_dashboard_stats(delivery_man)
        
        # Fetch active assignments for the dashboard
        active_assignments = LogisticsAssignment.objects.filter(
            pickup_or_delivery_man=delivery_man,
            delivery_status__in=['assigned', 'pickuped', 'in_transit']
        ).order_by('assignment_date')

        return render(request, "logistics_home.html", {
            'stats': stats,
            'user': delivery_man,
            'active_assignments': active_assignments
        })
    except DeliveryMan.DoesNotExist:
         return HttpResponse("<script>alert('User not found');window.location='/'</script>")


def register_delivery_man(request):
    if request.method == 'POST':
        # Collect form data
        first_name = request.POST['textfield10']
        last_name = request.POST['textfield12']
        housename = request.POST['textfield9']
        place = request.POST['textfield8']
        district = request.POST['textfield88']
        post = request.POST['textfield7']
        pin = request.POST['textfield6']
        email = request.POST['textfield5']
        phone = request.POST['textfield4']
        password1 = request.POST['textfield11']

        # File uploads
        profile_image = request.FILES.get('fileField')
        id_card = request.FILES.get('textfield13')

        # Validate file extensions
        allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf']
        if profile_image:
            profile_ext = profile_image.name.split('.')[-1].lower()
            if profile_ext not in allowed_extensions:
                messages.error(request, 'Invalid profile image type! Only JPG, JPEG, PNG, and PDF are allowed.')
                return render(request, 'register.html')
        
        if id_card:
            id_card_ext = id_card.name.split('.')[-1].lower()
            if id_card_ext not in allowed_extensions:
                messages.error(request, 'Invalid ID card type! Only JPG, JPEG, PNG, and PDF are allowed.')
                return render(request, 'register.html')

        # Save files to media directory
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')

        # Save profile image
        if profile_image:
            profile_filename = f"profile_{timestamp}.{profile_ext}"
            profile_path = os.path.join('logistics/profiles', profile_filename)  # Save in 'media/logistics/profiles/'
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            fs.save(profile_path, profile_image)
            profile_url = f"{settings.MEDIA_URL}{profile_path}"
        else:
            profile_url = None

        # Save ID card
        if id_card:
            id_card_filename = f"idcard_{timestamp}.{id_card_ext}"
            id_card_path = os.path.join('logistics/idcards', id_card_filename)  # Save in 'media/logistics/idcards/'
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            fs.save(id_card_path, id_card)
            id_card_url = f"{settings.MEDIA_URL}{id_card_path}"
        else:
            id_card_url = None

        # Check for existing user
        if login.objects.filter(username=email).exists():
            return HttpResponse("<script>alert('Already exists');window.location='/'</script>")

        # Create login entry
        log_obj = login(username=email, password=password1, usertype='logistics')
        log_obj.save()

        # Create delivery man entry
        delivery_man = DeliveryMan(
            first_name=first_name,
            last_name=last_name,
            house=housename,
            place=place,
            district=district,
            post=post,
            pin=pin,
            profile_image=profile_url,
            license_image=id_card_url,
            email=email,
            phone_number=phone,
            created_at=datetime.now(),
            LOGIN=log_obj
        )
        delivery_man.save()

        return HttpResponse("<script>alert('Registered successfully');window.location='/'</script>")

    return render(request, 'register.html')


def view_profile(request):
    usr_obj= DeliveryMan.objects.get(LOGIN=request.session['lid'])  # Assuming 'user' is a related field on the User model
    return render(request, 'profile_view.html', {'user': usr_obj})

def update_profile(request):
    usr_obj= DeliveryMan.objects.get(LOGIN=request.session['lid'])  # Assuming 'user' is a related field on the User model

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

        return redirect('profile_view')  # Redirect to the profile view page after update

    return render(request, 'profile_update.html', {'user': usr_obj})


from django.shortcuts import render
from user.models import LogisticsAssignment

def view_assigned_services(request):
    if 'lid' in request.session:
        login_id = request.session['lid']
        try:
            # Get the DeliveryMan instance using the login foreign key
            deliveryman = DeliveryMan.objects.get(LOGIN=login_id)
        except DeliveryMan.DoesNotExist:
            messages.error(request, "Delivery man not found.")
            return redirect('login')
        
        print(deliveryman.id)  # Now printing the deliveryman id
        
        # Get filter parameters from GET request
        selected_date = request.GET.get('date')
        status_filter = request.GET.get('status')
        
        # Filter assignments using the DeliveryMan instance
        services = LogisticsAssignment.objects.filter(
            pickup_or_delivery_man=deliveryman
        ).exclude(delivery_status='canceled')
        
        # Filter by date if provided
        if selected_date:
            services = services.filter(assignment_date__date=selected_date)
            
        # Filter by status if provided
        if status_filter:
            services = services.filter(delivery_status=status_filter)
        
        stats = get_dashboard_stats(deliveryman)

        context = {
            'assigned_services': services,
            'selected_date': selected_date,
            'status_filter': status_filter,
            'stats': stats, # Add stats to context
        }
        return render(request, 'assigned_services.html', context)
    else:
        messages.error(request, "Please log in first.")
        return redirect('login')


def mark_as_paid(request, payment_id):
    """
    Marks a Payment as paid (if it isn’t already) and bounces back
    to the referring page with a message.
    """
    payment = get_object_or_404(Payment, id=payment_id)

    if payment.payment_status != 'paid':
        payment.payment_status = 'paid'
        payment.save()
        messages.success(request, "💸 Payment marked as paid!")
    else:
        messages.info(request, "✅ This payment was already marked paid.")

    # Redirect back to the page where you clicked “Mark As Paid”
    return redirect(request.META.get('HTTP_REFERER', '/'))



from django.utils import timezone  # ✅ import this


@csrf_exempt
def update_dates(request, assignment_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pickup_date = data.get('pickup_date')
            delivery_date = data.get('delivery_date')

            assignment = LogisticsAssignment.objects.get(id=assignment_id)
            service_order = assignment.service_order

            # 🟢 Convert to timezone-aware datetime
            if pickup_date:
                service_order.pickup_date = timezone.make_aware(
                    timezone.datetime.fromisoformat(pickup_date)
                )
            if delivery_date:
                service_order.delivery_date = timezone.make_aware(
                    timezone.datetime.fromisoformat(delivery_date)
                )

            service_order.save()
            return JsonResponse({'message': 'Dates updated successfully!'})
        except LogisticsAssignment.DoesNotExist:
            return JsonResponse({'message': 'Assignment not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=400)


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import json
import threading

def send_email_async(recipient_email, subject, body):
    threading.Thread(target=send_email, args=(recipient_email, subject, body)).start()

def update_pickup_status(request, assignment_id):
    if request.method == 'POST':
        try:
            assignment = get_object_or_404(LogisticsAssignment, id=assignment_id)
            
            # Ensure only the assigned delivery man can update the status
            if request.session.get('lid') != assignment.pickup_or_delivery_man.LOGIN.id:
                return JsonResponse({'message': 'Unauthorized action.'}, status=403)

            data = json.loads(request.body)
            new_status = data.get('status')

            # Validate the status
            valid_statuses = ['assigned', 'pickuped', 'in_transit', 'delivered']
            if new_status not in valid_statuses:
                return JsonResponse({'message': 'Invalid status.'}, status=400)

            assignment.delivery_status = new_status
            assignment.save()

            # Determine the recipient email
            service_order = assignment.service_order
            if service_order.service_for == 'business' and service_order.BUSINESS:
                recipient_email = service_order.BUSINESS.business_email
                recipient_name = service_order.BUSINESS.owner_name
            elif service_order.service_for == 'user' and service_order.USER:
                recipient_email = service_order.USER.email
                recipient_name = service_order.USER.first_name
            else:
                recipient_email = None

            # Send email if recipient is found
            if recipient_email:
                subject = "Order Status Updated"

                body = f"""
                <html>
                <body>
                    <h2 style="color: #4CAF50;">Order Update Notification</h2>
                    <p>Dear {recipient_name},</p>
                    <p>Your order status has been updated to:</p>
                    <p style="font-weight: bold; color: #2196F3;">{new_status.capitalize()}</p>
                    <p>Thank you for choosing our service.</p>
                    <br>
                    <p style="font-size: small; color: #888;">This is an automated message. Please do not reply.</p>
                </body>
                </html>
                """  
            send_email_async(recipient_email, subject, body)
            return JsonResponse({'message': 'Status updated successfully!'})
            
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)




def open_scanner(request, service_order_id):
    return render(request, 'qr_scanner.html', {'service_order_id': service_order_id})



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



# def check_assign_bags(request, service_order_id):
#     if request.method == 'POST':
#         qr_code = request.POST.get('qr_code')
#         service_type = request.POST.get('service_type')
#         service_order = get_object_or_404(ServiceOrder, id=service_order_id)
#         user_instance = service_order.USER
#         num_bags_needed = user_instance.num_bags
#
#         # Check if the user has already been assigned the required number of bags
#         assigned_bags_count = LaundryBag.objects.filter(USER=user_instance).count()
#
#         # Check if the QR code already exists
#         existing_bag = LaundryBag.objects.filter(qr_code=qr_code).first()
#
#         # If the bag already exists, update its service type
#         if existing_bag:
#             existing_bag.service_type = service_type
#             existing_bag.save()
#             messages.success(request, "Laundry bag updated successfully!")
#
#         # If the QR code doesn't exist and the user hasn't reached the limit of bags
#         elif assigned_bags_count < num_bags_needed:
#             LaundryBag.objects.create(
#                 USER=user_instance,
#                 qr_code=qr_code,
#                 service_type=service_type
#             )
#             messages.success(request, "Laundry bag successfully assigned!")
#         else:
#             messages.error(request, "Cannot assign more bags than the required number.")
#             return HttpResponse("<script>alert('Cannot assign more bags than the required number.');window.location='/assigned-services'</script>")
#         return redirect('view_assigned_services')  # Redirect to a relevant page after submission
#
#     return render(request, 'qr_scanner.html', {'service_order_id': service_order_id})




def check_assign_bags(request, service_order_id):
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        service_type = request.POST.get('service_type')
        prefer=request.POST.get('prefer')
        service_order = get_object_or_404(ServiceOrder, id=service_order_id)

        # Determine which account to update along with a textual indicator for current service type
        if service_order.service_for == 'business' and service_order.BUSINESS:
            account = service_order.BUSINESS
            current_service = 'business'
        else:
            account = service_order.USER
            current_service = 'user'

        # Use the num_bags field from the relevant account
        num_bags_needed = account.num_bags

        # Check if this QR code is already assigned anywhere
        existing_assigned_bag = LaundryBag.objects.filter(qr_code=qr_code).first()
        if existing_assigned_bag:
            # Determine the service type used by the assigned bag
            # (Assuming that if the BUSINESS field is set, then it's a business assignment; otherwise, it's a user assignment)
            assigned_service = 'business' if existing_assigned_bag.BUSINESS else 'user'
            if assigned_service != current_service:
                messages.error(
                    request,
                    "This QR code is already assigned to a different service."
                )
                return HttpResponse(
                "<script>alert('This QR code is already assigned to a different service.');window.location='/assigned-services'</script>"
            )
            

        # If no existing bag with this QR code for any service, then check the number of bags already assigned to the current account.
        if current_service == 'business':
            assigned_bags_count = LaundryBag.objects.filter(BUSINESS=account).count()
        else:
            assigned_bags_count = LaundryBag.objects.filter(USER=account).count()

        if assigned_bags_count >= num_bags_needed:
            messages.error(request, "Cannot assign more bags than the required number.")
            return HttpResponse(
                "<script>alert('Cannot assign more bags than the required number.');window.location='/assigned-services'</script>"
            )

        # Create a new bag if limit hasn't been reached
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



def assign_bag_with_qr(request, service_order_id):
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        service_type = request.POST.get('service_type')
        service_order = get_object_or_404(ServiceOrder, id=service_order_id)
        user = service_order.USER

        # Check if the QR code is already used
        if LaundryBag.objects.filter(qr_code=qr_code).exists():
            messages.error(request, "This QR code is already assigned.")
            return redirect('open_scanner')

        # Assign the bag
        LaundryBag.objects.create(
            USER=user,
            bag_number=user.num_bags + 1,
            qr_code=qr_code,
            service_type=service_type
        )
        messages.success(request, "Bag successfully assigned!")
        return redirect('check_assign_bags', service_order_id=service_order.id)

from django.utils import timezone

def deliveryman_pending_orders(request):
    # Get the logged-in delivery man's login id from session
    login_id = request.session.get('lid')
    if not login_id:
        return redirect("login")

    try:
        current_delivery_man = DeliveryMan.objects.get(LOGIN__id=login_id)
    except DeliveryMan.DoesNotExist:
        return redirect("login")

    # Use consistent status casing (using "pending" in this case)
    pending_orders = ServiceOrder.objects.filter(status="pending")
    
    stats = get_dashboard_stats(current_delivery_man)

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        if not order_id:
            return render(request, "deliveryman_pending_orders.html", {
                "pending_orders": pending_orders,
                "delivery_man": current_delivery_man,
                "error": "No order selected.",
                "stats": stats
            })

        # Ensure the order exists and is still pending (use "pending")
        order = get_object_or_404(ServiceOrder, id=order_id, status="pending")

        # Create or update the LogisticsAssignment record for the order
        logistics_assignment, created = LogisticsAssignment.objects.get_or_create(service_order=order)
        logistics_assignment.pickup_or_delivery_man = current_delivery_man
        logistics_assignment.assignment_date = timezone.now()
        logistics_assignment.delivery_status = "assigned"
        logistics_assignment.save()

        # Update the service order status to "pickup_assigned"
        order.status = "pickup_assigned"
        order.save()

        return redirect("deliveryman_pending_orders")

    return render(request, "deliveryman_pending_orders.html", {
        "pending_orders": pending_orders,
        "delivery_man": current_delivery_man,
        "stats": stats
    })


