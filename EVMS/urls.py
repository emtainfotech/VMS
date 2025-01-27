from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',vendor_signup,name = 'vendor_signup'),
    path('vendor-signup/',vendor_signup,name = 'vendor_signup'),
    path('vendor-login/',vendor_login,name = 'vendor_login'),
    path('vendor-logout/', vendor_logout, name='vendor_logout'),
    path('vendor-dashboard/',vendor_dashboard,name = 'vendor_dashboard'),
    path('vendor-profile/<int:id>/',vendor_profile,name = 'vendor_profile'),
    path('candidateform/', candidate_form, name='candidate_form'),
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)