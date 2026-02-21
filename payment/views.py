from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Sum
from myadmin.models import login
from user.models import Payment, Subscription, user as UserModel
from business.models import Business
from django.contrib import messages



import csv
from django.http import HttpResponse # Added for CSV export
from decimal import Decimal

from django.core.paginator import Paginator

def payment_history(request):
    if 'lid' not in request.session:
        return redirect('login')

    login_id = request.session['lid']
    try:
        login_instance = login.objects.get(id=login_id)
    except login.DoesNotExist:
        return redirect('login')

    # Determine if this login is tied to a user or a business
    user_instance = None
    business_instance = None

    try:
        user_instance = UserModel.objects.get(LOGIN=login_instance)
    except UserModel.DoesNotExist:
        try:
            business_instance = Business.objects.get(LOGIN=login_instance)
        except Business.DoesNotExist:
            return redirect('login')  # Invalid login

    # Fetch payments and subscriptions
    if user_instance:
        payments_query = Payment.objects.filter(service_order__USER=user_instance).order_by('-created_at')
        subscriptions_query = Subscription.objects.filter(subscription_for='user', user=user_instance)
    else:
        payments_query = Payment.objects.filter(service_order__BUSINESS=business_instance).order_by('-created_at')
        subscriptions_query = Subscription.objects.filter(subscription_for='business', business=business_instance)

    # Filtering Logic
    service_type = request.GET.get('service_type')
    payment_status = request.GET.get('payment_status')

    if service_type:
        payments_query = payments_query.filter(service_order__service_type=service_type)
    if payment_status:
        payments_query = payments_query.filter(payment_status=payment_status)

    # CSV Export Logic (Exports all filtered data, ignoring pagination)
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payment_history.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date & Time', 'Service', 'Amount', 'Status', 'Payment Date'])
        for p in payments_query:
            amount = f"INR {p.total_price}" if not p.service_order.subscription else "Subscription"
            writer.writerow([
                p.service_order.order_date.strftime('%Y-%m-%d %H:%M'),
                p.service_order.service_type,
                amount,
                p.payment_status,
                p.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        return response

    # Pagination Logic
    paginator = Paginator(payments_query, 5) # Show 5 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Base counts and totals (independent of filters for stats)
    if user_instance:
        base_payments = Payment.objects.filter(service_order__USER=user_instance)
    else:
        base_payments = Payment.objects.filter(service_order__BUSINESS=business_instance)
    
    total_spent = base_payments.filter(payment_status='paid').aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    subscription_total = subscriptions_query.aggregate(total=Sum('subscription_plan__price'))['total'] or Decimal('0.00')
    
    total_spent = total_spent.quantize(Decimal('0.01'))
    subscription_total = subscription_total.quantize(Decimal('0.01'))
    combined_total = (total_spent + subscription_total).quantize(Decimal('0.01'))

    # Progress Calculation (Dummy logic for percentages based on relative contribution or targets)
    # 1. Total Spent Pct: Let's assume a dummy monthly budget target of 5000 for visuals
    target = Decimal('5000.00')
    total_spent_pct = min(100, int((total_spent / target) * 100)) if target > 0 else 0
    
    # 2. Subscription Total Pct: Relative to combined total
    sub_pct = min(100, int((subscription_total / combined_total * 100))) if combined_total > 0 else 0
    
    # 3. Last payment pct (just a visual representation of completeness)
    last_payment_pct = 100 if payments_query.exists() else 0

    context = {
        'payments': page_obj, # Pass page_obj instead of queryset
        'total_spent': total_spent,
        'subscriptions': subscriptions_query,
        'subscription_total': subscription_total,
        'subscription_count': subscriptions_query.count(),
        'combined_total': combined_total,
        'total_spent_pct': total_spent_pct,
        'sub_pct': sub_pct,
        'last_payment_pct': last_payment_pct,
        'current_service': service_type or '',
        'current_status': payment_status or '',
    }

    return render(request, 'payment_history.html', context)
