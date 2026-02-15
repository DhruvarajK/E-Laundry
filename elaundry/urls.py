from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include("myadmin.urls")),
    path('',include("user.urls")),
    path('',include("payment.urls")),
    path('',include("business.urls")),
    path('',include("logistics.urls")),
]
