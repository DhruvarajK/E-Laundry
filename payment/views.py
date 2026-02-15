from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Sum
from myadmin.models import login
from user.models import Payment, Subscription, user as UserModel
from business.models import Business
from django.contrib import messages



from decimal import Decimal


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
        payments = Payment.objects.filter(service_order__USER=user_instance).order_by('-created_at')
        subscriptions = Subscription.objects.filter(subscription_for='user', user=user_instance)
    else:
        payments = Payment.objects.filter(service_order__BUSINESS=business_instance).order_by('-created_at')
        subscriptions = Subscription.objects.filter(subscription_for='business', business=business_instance)

    # Calculate totals with rounding to 2 decimal places
    total_spent = payments.aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
    subscription_total = subscriptions.aggregate(total=Sum('subscription_plan__price'))['total'] or Decimal('0.00')

    # Ensure totals are rounded to 2 decimals
    total_spent = total_spent.quantize(Decimal('0.01'))
    subscription_total = subscription_total.quantize(Decimal('0.01'))

    combined_total = (total_spent + subscription_total).quantize(Decimal('0.01'))
    subscription_count = subscriptions.count()

    context = {
        'payments': payments,
        'total_spent': total_spent,
        'subscriptions': subscriptions,
        'subscription_total': subscription_total,
        'subscription_count': subscription_count,
        'combined_total': combined_total,
    }

    return render(request, 'payment_history.html', context)
