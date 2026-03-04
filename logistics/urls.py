
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from myadmin.views import logout

urlpatterns = [
    path('logistics_home/profile/', views.view_profile, name='profile_view'), 
    path('logistics_home/profile/update/', views.update_profile, name='profile_update'),
    path('logistics_home/', views.logistics_home, name='logistics_home'),
    path('register_delivery/', views.register_delivery_man, name='register_delivery'),
    path('assigned-services/', views.view_assigned_services, name='view_assigned_services'),
    path('update_pickup_status/<int:assignment_id>/', views.update_pickup_status, name='update_pickup_status'),
    path('logout/', logout, name='logout'),
    path('camera/', views.camera, name='camera'),
    path('open_scanner/', views.open_scanner, name='open_scanner'),
    # path('assign-bag-with-qr/<int:service_order_id>/', views.assign_bag_with_qr, name='assign_bag_with_qr'),
    path('check_assign_bags/<int:service_order_id>/', views.check_assign_bags, name='check_assign_bags'),
    path('get_bag_details/', views.get_bag_details, name='get_bag_details'),
    path('deliveryman_pending_orders/', views.deliveryman_pending_orders, name='deliveryman_pending_orders'),
    path('update_dates/<int:assignment_id>/', views.update_dates, name='update_dates'),
    path('payment/<int:payment_id>/mark-paid/', views.mark_as_paid,name='mark_as_paid' ),
    path('earnings/', views.view_earnings, name='earnings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

