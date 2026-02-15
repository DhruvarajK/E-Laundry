from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from user.models import LogisticsAssignment, Payment, ServiceOrder, Subscription


class Command(BaseCommand):
    help = 'Generate daily service orders for active subscriptions'

    def handle(self, *args, **options):
        now = timezone.now()
        # if time(9, 0) <= now.time() <= time(11, 0):
        if time(0, 0) <= now.time() <= time(23, 59):  # Runs all day

            active_subscriptions = Subscription.objects.filter(is_active=True, end_date__gte=now)
            for subscription in active_subscriptions:
                order = ServiceOrder.objects.create(  # Store the created order in a variable
                    service_for=subscription.subscription_for,
                    USER=subscription.user if subscription.subscription_for == 'user' else None,
                    BUSINESS=subscription.business if subscription.subscription_for == 'business' else None,
                    subscription=subscription,
                    service_type=subscription.subscription_plan.service_type,
                )
                LogisticsAssignment.objects.create(service_order=order)
                payment = Payment.objects.create(
                    service_order=order,
                    payment_status='Paid',
                    total_price=0
                )
                payment.save()

                subscription.remaining_services -= 1
                if subscription.remaining_services <= 0:
                    subscription.is_active = False
                subscription.save()

            self.stdout.write("Daily service orders generated successfully.")
        else:
            self.stdout.write("Outside order generation window.")
