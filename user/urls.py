from django.conf import settings
from django.urls import path
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('view_profile_user/', views.view_profile_user, name='view_profile_user'),  # View Profile
    path('update_profile_user/', views.update_profile_user, name='update_profile_user'),
    path('register/', views.register_user, name='register_user'),
    path('get-location/', views.get_current_location, name='get_current_location'),
    path('user_home/normal_order/', views.normal_order, name='normal_order'),
    path('user_home/order_confirmed/<int:order_id>/', views.order_confirmed, name='order_confirmed'),
    path('user_home/', views.user_home, name='user_home'),
    path('track_orders/', views.track_orders, name='track_orders'),
    path('view_all_orders/', views.view_all_orders, name='view_all_orders'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'), 
    path('camera/', views.camera, name='camera'),
    path('open_scanner/', views.open_scanner, name='open_scanner'),
    path('assign-bag-with-qr/<int:service_order_id>/', views.assign_bag_with_qr, name='assign_bag_with_qr'),
    path('subscriptions/', views.subscription_plans, name='subscription_plans'),
    path('subscription_details/', views.subscription_details, name='subscription_details'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('subscription-confirmed/<int:subscription_id>/', views.subscription_confirmed, name='subscription_confirmed'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('scan-qr/', views.scan_qr_page, name='scan_qr_page'),
    path('process-camera/', views.process_camera, name='process_camera'),
    path('bag-details/', views.bag_details, name='bag_details'),
    path('razorpay-payment/<int:order_id>/', views.razorpay_payment, name='razorpay_payment'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('about-us/', views.about_us, name='about_us'),
]
     

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)