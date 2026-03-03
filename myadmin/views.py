from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from business.models import Business
from logistics.models import DeliveryMan
from .models import Feedback, login
from django.db.models import Q,Count
from user.models import BillItem, Machine, Payment, Subscription, SubscriptionPlan, user
from django.shortcuts import render, redirect, get_object_or_404
from user.models import ServiceOrder,LogisticsAssignment
from django.urls import reverse
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
from .auth_check import login_required

load_dotenv()


def index(request):
    if 'lid' in request.session and request.session['lid'] != 'out':
        try:
            res = login.objects.get(id=request.session['lid'])
            if res.usertype == "admin":
                return redirect('/admin_home')
            elif res.usertype == "logistics":
                return redirect('/logistics_home')
            elif res.usertype == "user":
                return redirect('/user_home')
            elif res.usertype == "business":
                return redirect('/business_home')
        except login.DoesNotExist:
            pass
    return render(request,"main_index.html")

def login_return(request):
    if 'lid' in request.session and request.session['lid'] != 'out':
        try:
            res = login.objects.get(id=request.session['lid'])
            if res.usertype == "admin":
                return redirect('/admin_home')
            elif res.usertype == "logistics":
                return redirect('/logistics_home')
            elif res.usertype == "user":
                return redirect('/user_home')
            elif res.usertype == "business":
                return redirect('/business_home')
        except login.DoesNotExist:
            pass
    return render(request,"login.html")

def login_post(request):
    username = request.POST['textfield']
    password = request.POST['textfield2']
    try:
        res = login.objects.get(username=username)
        if check_password(password, res.password):
            if res.usertype =="admin":
                request.session['lid'] = res.id
                return redirect('/admin_home')
            elif res.usertype == "logistics":
                request.session['lid'] = res.id
                return redirect('/logistics_home')
            elif res.usertype == "user":
                request.session['lid'] = res.id
                return redirect('/user_home')
            elif res.usertype == "business":
                request.session['lid'] = res.id
                return redirect('/business_home')
            else:
                return render(
                    request,
                    "login.html",
                    {"error": "Invalid user type."}
                )
        else:
            raise login.DoesNotExist
    except login.DoesNotExist:
        return render(
            request,
            "login.html",
            {
                "error": "Invalid username or password.",
            }
        )
def get_logged_in_user(request):
    user_id = request.session.get('lid')
    if user_id:
        try:
            return login.objects.get(id=user_id)
        except login.DoesNotExist:
            return None
    return None

def logout(request):
    request.session['lid'] = 'out'
    return HttpResponse("<script>window.location='/'</script>")
    # return redirect('/')

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Create plain text fallback
        text = """Welcome to Azoria AI! Please enable HTML to view this email."""
        html = body
        
        # Attach both versions
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
            
    except smtplib.SMTPException as e:
        print(f"SMTP error sending to {to_email}: {e}")
    except Exception as e:
        print(f"General error sending to {to_email}: {e}")

@login_required
def view_pending_deliverymen(request):
    data = DeliveryMan.objects.filter(LOGIN__usertype="pending")
    return render(request,"pending_deliveryman.html",{"pending_deliverymen":data})



@login_required
def view_users(request):
    # data = user.objects.filter(LOGIN__usertype="user")
    data = user.objects.filter(Q(LOGIN__usertype="user") | Q(LOGIN__usertype="block"))
    return render(request,"view_user.html",{"data":data})

@login_required
def view_logistics(request):
     data = DeliveryMan.objects.filter(Q(LOGIN__usertype="logistics") | Q(LOGIN__usertype="block"))
     return render(request,'view_logistics.html',{"data":data})

@login_required
def view_business(request):
     data = Business.objects.filter(Q(LOGIN__usertype="business") | Q(LOGIN__usertype="block"))
     return render(request,'view_business.html',{"data":data})

@login_required
def accept(request,id):
    login.objects.filter(id=id).update(usertype='logistics')
    return HttpResponse("<script>alert('logistics accepted');window.location='/pending_deliverymen/'</script>")

@login_required
def reject(request,id):
     login.objects.filter(id=id).delete()
     return HttpResponse("<script>alert('logistics rejected');window.location='/pending_deliverymen/'</script>")


@login_required
def admin_home(request):
    
    # 1. Total Revenue (Paid payments)
    revenue_data = Payment.objects.filter(payment_status='paid').aggregate(total=Sum('total_price'))
    total_revenue = revenue_data['total'] or 0

    # 2. Active Jobs (Not completed or canceled)
    active_jobs_count = ServiceOrder.objects.exclude(status__in=['completed', 'canceled', 'Completed', 'Canceled']).count()
    
    # 3. Pending Pickup (Status: pending or pickup_assigned)
    pending_pickup_count = ServiceOrder.objects.filter(status__in=['pending', 'pickup_assigned']).count()

    # 4. Machine Usage (Simulated by Orders in 'Washing' status)
    washing_count = ServiceOrder.objects.filter(status__in=['Washing', 'washing']).count()
    # Assuming slight variety to make it look like a percentage if generic, 
    # but for now let's just use the count or mapped percentage. 
    # Let's say max capacity is 20 for demo purposes.
    machine_usage_percent = min(int((washing_count / 20) * 100), 100) if washing_count else 0

    # 5. Logistics (Courier count)
    logistics_count = DeliveryMan.objects.filter(LOGIN__usertype='logistics').count()
    
    # 6. Couriers En Route (Assigned/In Transit)
    couriers_en_route = LogisticsAssignment.objects.filter(delivery_status__in=['assigned', 'pickuped', 'in_transit']).count()

    # 7. Incoming Jobs (Pending orders, limit 5)
    incoming_jobs = ServiceOrder.objects.filter(status='pending').order_by('-order_date')[:5]

    # 8. Live Operations (Active orders with time elapsed)
    # We'll fetch active orders and calculate time elapsed in template or here.
    live_operations = ServiceOrder.objects.filter(status__in=['Washing', 'washing', 'in_progress']).order_by('-order_date')[:4]

    # 9. Revenue Chart Data (Last 12 intervals/hours/days? Let's do days for simplicity or dummy specific distribution)
    # For now, let's just pass some data or calculate daily revenue for last 7 days.
    # Simple chart data: Today's revenue by hour (simulated or real if enough data)
    # Let's do last 7 days revenue.
    
    today = timezone.now().date()
    revenue_chart_data = []
    for i in range(11, -1, -1): # Last 12 days including today? Or 12 data points
        day = today - timedelta(days=i)
        daily_revenue = Payment.objects.filter(
            payment_status='paid',
            created_at__date=day
        ).aggregate(total=Sum('total_price'))['total'] or 0
        revenue_chart_data.append({
            'day': day.strftime("%d"),
            'revenue': float(daily_revenue),
            'height_percent': min(int((daily_revenue / (total_revenue or 1)) * 100 * 5), 100) if total_revenue else 0 # simple scaling
        })

    context = {
        'total_revenue': total_revenue,
        'active_jobs_count': active_jobs_count,
        'pending_pickup_count': pending_pickup_count,
        'machine_usage_percent': machine_usage_percent,
        'logistics_count': logistics_count,
        'couriers_en_route': couriers_en_route,
        'incoming_jobs': incoming_jobs,
        'live_operations': live_operations,
        'revenue_chart_data': revenue_chart_data,
    }

    return render(request, "admin_home.html", context)



@login_required
def block(request,id):
     login.objects.filter(id=id).update(usertype='block')
     return HttpResponse("<script>alert('blocked');window.location='/admin_home/'</script>")

@login_required
def unblock(request,id):
      login.objects.filter(id=id).update(usertype='logistics')
      return HttpResponse("<script>alert('logistics unblocked');window.location='/view_logistics/'</script>")

@login_required
def businessunblock(request,id):
      login.objects.filter(id=id).update(usertype='business')
      return HttpResponse("<script>alert('business unblocked');window.location='/view_business/'</script>")




@login_required
def userunblock(request,id):
      login.objects.filter(id=id).update(usertype='user')
      return HttpResponse("<script>alert('user unblocked');window.location='/view_users/'</script>")

# def admin_viewrequirements(request):
#     if request.session['lid'] == 'out':
#         return HttpResponse("<script>alert('please login');window.location='/'</script>")
#     else:
#         return render(request,"viewrequirements.html")

# def admin_viewuser(request):
#     if request.session['lid'] == 'out':
#         return HttpResponse("<script>alert('please login');window.location='/'</script>")
#     else:
#          data = user.objects.all()
#          return render(request,"view_user.html",{"data":data})





# Manage Logistics #



def pending_service_orders(request):
    """
    Fetch all pending service orders and display them on the pending orders page.
    """
    pending_orders = ServiceOrder.objects.filter(status="pending")  # Get all pending orders
    return render(request, "admin_pending_orders.html", {"pending_orders": pending_orders})




from django.utils import timezone  

from django.shortcuts import render, redirect
import threading

def send_email_async(recipient_email, subject, body):
    threading.Thread(target=send_email, args=(recipient_email, subject, body)).start()

def assign_delivery_man(request, order_id):
    order = ServiceOrder.objects.get(id=order_id)
    delivery_men = DeliveryMan.objects.all()  # Fetch delivery men
    
    if request.method == "POST":
        # Get the selected delivery man from the POST request
        delivery_man_id = request.POST.get("delivery_man_id")
        print(f"Received delivery_man_id: {delivery_man_id}")  # Debug print

        try:
            delivery_man = DeliveryMan.objects.get(id=delivery_man_id)
            print(f"Assigned Delivery Man: {delivery_man}")  # Debug print

            # Create or update the LogisticsAssignment
            logistics_assignment, created = LogisticsAssignment.objects.get_or_create(service_order=order)
            print(f"LogisticsAssignment: {logistics_assignment}")  # Debug print
            
            # Update the service order status
            order.status = "Pickup Assigned"  
            order.save()
            
            # Update logistics assignment fields
            logistics_assignment.pickup_or_delivery_man = delivery_man
            logistics_assignment.assignment_date = timezone.now()  # Use timezone-aware datetime
            logistics_assignment.delivery_status = "assigned"  # Or whatever status you want to set
            logistics_assignment.save()
            print(f"LogisticsAssignment saved with delivery man: {logistics_assignment.pickup_or_delivery_man} and status: {logistics_assignment.delivery_status}")  # Debug print

            # Prepare email notification to the delivery man
            subject = f"New Pickup Assignment from eLaundry Order #{order.id}"
            body = f"""
            <html>
                <body>
                    <h2>New Order Assignment</h2>
                    <p>Dear {delivery_man.first_name},</p>
                    <p>You have been assigned to pick up an order from eLaundry.</p>
                    <p><strong>Order ID:</strong> {order.id}</p>
                    <p><strong>Order Type:</strong> {order.service_type}</p>
                    <p><strong>Service For:</strong> {order.service_for}</p>
                    <p><strong>Instructions:</strong> {order.special_instructions}</p>
                    <p>Please log in to your dashboard for more details and confirm the pickup.</p>
                    <br>
                    <p>Regards,<br>eLaundry Team</p>
                </body>
            </html>
            """
            
            send_email_async(delivery_man.email, subject, body)
            
            return redirect("pending_service_orders")
        except DeliveryMan.DoesNotExist:
            return render(request, "assign_delivery_man.html", {"order": order, "delivery_men": delivery_men, "error": "Delivery man not found."})
    
    print(f"Order: {order}")
    print(f"Delivery Men: {list(delivery_men)}")
    
    return render(request, "assign_delivery_man.html", {"order": order, "delivery_men": delivery_men})


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone



def assigned_orders(request):
    assignments = LogisticsAssignment.objects.filter(delivery_status='assigned')
    context = {
        'assignments': assignments,
    }
    print(context)
    return render(request, 'assigned_orders.html', context)


def unassign_logistics(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    try:
        logistics_assignment = LogisticsAssignment.objects.get(service_order=order)
        logistics_assignment.delete()
        order.status = 'pending'
        order.save()
    except LogisticsAssignment.DoesNotExist:
        pass

    return redirect('assigned_orders')




def update_order_status(request):
    # Check if "hide_completed" filter is applied
    hide_completed = request.GET.get("hide_completed", "false").lower() == "true"

    # Filter orders based on the hide_completed flag
    if hide_completed:
        orders = ServiceOrder.objects.exclude(status__in=["completed", "Completed", "canceled", "Canceled"])
    else:
        orders = ServiceOrder.objects.exclude(status__in=["canceled", "Canceled"])

    if request.method == "POST":
        selected_order_ids = request.POST.getlist("order_ids")
        new_status = request.POST.get("new_status")

        if new_status not in ["Washing", "Completed","in progress"]:
            return render(request, "update_order_status.html", {
                "orders": orders,
                "error": "Invalid status selection.",
                "hide_completed": hide_completed,
            })

        # Update the status of selected orders
        for order_id in selected_order_ids:
            order = get_object_or_404(ServiceOrder, id=order_id)
            
            # Loyalty points logic: award points if status changes specifically to 'Completed'
            if new_status == "Completed" and order.status != "Completed":
                if order.service_for == 'user' and order.USER:
                    usr_obj = order.USER
                    points_to_add = 20 # Base points for completion
                    
                    # Additional points based on payment if total_price exists
                    payment = getattr(order, 'payment', None)
                    if payment and payment.payment_status == 'paid':
                        points_to_add += int(payment.total_price)
                    
                    usr_obj.loyalty_points += points_to_add
                    usr_obj.save()

            order.status = new_status
            order.save()

        return redirect(f"/update-order-status/?hide_completed={'true' if hide_completed else 'false'}")

    context = {
        "orders": orders,
        "hide_completed": hide_completed,
    }
    return render(request, "update_order_status.html", context)

def admin_generate_bill(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)

    if request.method == "POST":
        cloth_types = request.POST.getlist("cloth_type[]")
        quantities = request.POST.getlist("quantity[]")
        prices = request.POST.getlist("price_per_item[]")

        # Remove old bill items for this order (if any)
        BillItem.objects.filter(service_order=order).delete()

        # Create new bill items
        for cloth_type, quantity, price in zip(cloth_types, quantities, prices):
            if cloth_type and quantity.isdigit() and price.replace('.', '', 1).isdigit():
                BillItem.objects.create(
                    service_order=order,
                    cloth_type=cloth_type,
                    quantity=int(quantity),
                    price_per_item=float(price)
                )

        messages.success(request, "Bill generated successfully!")
        return redirect("view_bill", order_id=order.id)

    bill_items = BillItem.objects.filter(service_order=order)
    return render(request, "admin_generate_bill.html", {"order": order, "bill_items": bill_items})

def bill_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    bill = payment.generate_bill()
    return render(request, "bill_detail.html", {"bill": bill})

def generate_bill_view(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    payment = order.payment  # Assuming a one-to-one relationship exists

    if request.method == 'POST':
        # Collect bill items from the form (dynamically named)
        bill_items = []
        total_price = 0  # To track the total price of all bill items
        index = 1
        while f'item_type_{index}' in request.POST:
            item_type = request.POST.get(f'item_type_{index}')
            quantity = request.POST.get(f'quantity_{index}')
            price = request.POST.get(f'price_{index}')
            if item_type and quantity and price:
                bill_items.append({
                    'item_type': item_type,
                    'quantity': int(quantity),
                    'price': float(price),
                })
                total_price += int(quantity) * float(price)  # Add the total cost for this item

            index += 1

        # Save each bill item
        for item in bill_items:
            BillItem.objects.create(
                payment=payment,
                item_type=item['item_type'],
                quantity=item['quantity'],
                price_per_item=item['price']
            )

        # Update the total price in the Payment model
        payment.total_price = total_price
        payment.save()

        # Redirect to the bill detail page
        messages.success(request, "Bill generated and total price updated successfully.")
        return redirect('bill_detail', payment_id=payment.id)

    return render(request, "generate_bill.html", {"order": order, "payment": payment})


def bill_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    bill = payment.generate_bill()
    return render(request, "bill_detail.html", {"bill": bill})

def view_bill(request, order_id):
    order = get_object_or_404(ServiceOrder, id=order_id)
    payment = order.payment  
    bill_items = BillItem.objects.filter(payment=payment)

    # Sum total prices using the @property from BillItem
    total_price = sum(item.total_price for item in bill_items)

    # Retrieve the logged-in user instance from session
    login_instance = None
    if 'lid' in request.session:
        login_instance = login.objects.get(id=request.session['lid'])

    # When the user submits the form with a chosen payment option
    if request.method == 'POST':
        payment_option = request.POST.get('payment_option')
        if payment_option == 'pay_now':
            # Redirect to dummy Razorpay payment page, passing the order_id
            return redirect('razorpay_payment', order_id=order.id)
        elif payment_option == 'cod':
            # For COD, we keep the payment as pending (or update as needed)
            payment.payment_status = 'pending'
            payment.save()
            # Then redirect to a payment success page (or a COD confirmation page)
            return redirect('payment_success', order_id=order.id)
            
    return render(request, "view_bill.html", {
        "order": order,
        "bill_items": bill_items,
        "total_price": total_price,
        "login_instance": login_instance  # Pass the login instance to the template
    })


def create_subscription_plan(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        duration_days = request.POST.get('duration_days')
        max_services = request.POST.get('max_services')
        service_type= request.POST.get('service_type')
        description = request.POST.get('description', '')

        SubscriptionPlan.objects.create(
            name=name,
            price=price,
            duration_days=int(duration_days),
            max_services=int(max_services),
            service_type=service_type,
            description=description
        )
        return redirect('list_subscription_plans')  # Adjust the URL name as needed
    
    return render(request, 'create_subscription_plan.html')

def delete_subscription_plan(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    if request.method == 'POST':
        plan.delete()
        return redirect('list_subscription_plans')
    return render(request, 'delete_subscription_plan.html', {'plan': plan})

def list_subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'list_subscription_plans.html', {'plans': plans})

def service_order_report(request):
    # Get filter parameters from query string
    date_filter = request.GET.get('date', '')
    service_for_filter = request.GET.get('service_for', 'all')
    
    orders = ServiceOrder.objects.all()
    filter_date = None
    user_total = Subscription.objects.filter(
        subscription_for='user'
    ).aggregate(total=Sum('subscription_plan__price'))['total'] or 0

    business_total = Subscription.objects.filter(
        subscription_for='business'
    ).aggregate(total=Sum('subscription_plan__price'))['total'] or 0

    # Filter by date if provided
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            orders = orders.filter(order_date__date=filter_date)
        except ValueError:
            filter_date = None  # You can add error handling if needed

    # Filter by service_for if provided (user, business, or all)
    if service_for_filter in ['user', 'business']:
        orders = orders.filter(service_for=service_for_filter)

    # Summary stats
    total_orders = orders.count()
    user_service_count = orders.filter(service_for='user').count()
    business_service_count = orders.filter(service_for='business').count()

    # Total revenue for orders with paid payments
    revenue_data = Payment.objects.filter(
        service_order__in=orders, 
        payment_status='paid'
    ).aggregate(total=Sum('total_price'))
    total_revenue = revenue_data['total'] or 0

    context = {
        'orders': orders,
        'filter_date': date_filter,
        'total_orders': total_orders,
        'user_service_count': user_service_count,
        'business_service_count': business_service_count,
        'total_revenue': total_revenue,
        'service_for_filter': service_for_filter,
        'user_total': user_total,
        'business_total': business_total,
        'grand_total': user_total + business_total,
    }
    return render(request, 'service_order_report.html', context)


def update_bags(request):
    # Get filter type: either 'user' or 'business'
    filter_type = request.GET.get('filter', 'user')
    search_query = request.GET.get('search', '')

    # Filter objects based on type and search query
    if filter_type == 'user':
        objects = user.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    else:
        objects = Business.objects.filter(
            Q(business_name__icontains=search_query) |
            Q(owner_name__icontains=search_query) |
            Q(business_email__icontains=search_query)
        )

    # If it's a POST request, update the number of bags for the selected object
    if request.method == 'POST':
        obj_id = request.POST.get('object_id')
        new_num_bags = request.POST.get('num_bags')
        # Make sure to validate new_num_bags as needed
        if filter_type == 'user':
            obj = get_object_or_404(user, id=obj_id)
        else:
            obj = get_object_or_404(Business, id=obj_id)
        obj.num_bags = new_num_bags
        obj.save()
        return redirect('update_bags')  # Change this to your URL name if different

    context = {
        'objects': objects,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    return render(request, 'update_bags.html', context)

# feedback

def feedback_list(request):
    current_user = get_logged_in_user(request)
    if not current_user:
        return redirect('/')  # or wherever your login page is
    
    # Admin sees all feedback, others only see their own
    if current_user.usertype == 'admin':
        feedbacks = Feedback.objects.all().order_by('-created_at')
    else:
        feedbacks = Feedback.objects.filter(user=current_user).order_by('-created_at')
    return render(request, 'feedback_list.html', {'feedbacks': feedbacks, 'user': current_user})

def add_feedback(request):
    current_user = get_logged_in_user(request)
    if not current_user:
        return redirect('/')
    
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            Feedback.objects.create(user=current_user, message=message)
        return redirect('feedback_list')
    return render(request, 'add_feedback.html')

def reply_feedback(request, feedback_id):
    current_user = get_logged_in_user(request)
    if not current_user or current_user.usertype != 'admin':
        return redirect('feedback_list')
    
    feedback = get_object_or_404(Feedback, id=feedback_id)
    
    if request.method == 'POST':
        reply = request.POST.get('reply')
        if reply:
            feedback.admin_reply = reply
            feedback.replied_at = timezone.now()
            feedback.save()
        return redirect('feedback_list')
    
    return render(request, 'reply_feedback.html', {'feedback': feedback})





def track_delivery_works(request):
    # Get the selected date from the GET parameter, defaulting to today.
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()


    deliverymen = DeliveryMan.objects.annotate(
        work_count_today=Count(
            'pickup_orders',
            filter=Q(pickup_orders__assignment_date__date=selected_date)
        ),
        total_work_count=Count('pickup_orders')
    )

    context = {
        'deliverymen': deliverymen,
        'selected_date': selected_date
    }
    return render(request, 'track_delivery_works.html', context)

@login_required
def manage_machines(request):
    machines = Machine.objects.all()
    return render(request, 'manage_machines.html', {'machines': machines})

@login_required
def add_machine(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        capacity = request.POST.get('capacity')
        is_active = request.POST.get('is_active') == 'on'
        
        Machine.objects.create(
            name=name,
            capacity=float(capacity),
            is_active=is_active
        )
        messages.success(request, 'Machine added successfully!')
        return redirect('manage_machines')
    
    return render(request, 'add_machine.html')

@login_required
def edit_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    if request.method == 'POST':
        machine.name = request.POST.get('name')
        machine.capacity = float(request.POST.get('capacity'))
        machine.is_active = request.POST.get('is_active') == 'on'
        machine.save()
        messages.success(request, 'Machine updated successfully!')
        return redirect('manage_machines')
    
    return render(request, 'add_machine.html', {'machine': machine})

@login_required
def delete_machine(request, machine_id):
    machine = get_object_or_404(Machine, id=machine_id)
    machine.delete()
    messages.success(request, 'Machine deleted successfully!')
    return redirect('manage_machines')

def error_404_view(request, exception):
    return render(request, '404.html', status=404)

def contact(request):
    return render(request, 'contact.html')
