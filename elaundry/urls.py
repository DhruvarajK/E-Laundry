from django.contrib import admin
from django.urls import path,include
from .views import health_check
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico')),
    path('',include("myadmin.urls")),
    path('',include("user.urls")),
    path('',include("payment.urls")),
    path('',include("business.urls")),
    path('',include("logistics.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
