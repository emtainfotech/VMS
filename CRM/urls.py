from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',custom_admin_login,name = 'custom_admin_login'),
    path('crm-dashboard/',crm_dashboard,name = 'crm_dashboard'),
    path('admin-candidate-registration/',admin_candidate_registration,name = 'admin_candidate_registration'),
    path('candidate-list/',admin_candidate_list,name = 'admin_candidate_list'),
    path('candidate-details/<int:id>/', admin_candidate_profile, name='candidate-details'),
    path('admin-company-list/',admin_company_list,name = 'admin_company_list'),
    path('admin-company-registration/',admin_company_registration,name = 'admin_company_registration'),
    path('admin-company-profile/<int:id>/', admin_company_profile, name='admin_company_profile'),
    path('admin-vendor-list/',admin_vendor_list,name = 'admin_vendor_list'),
    path('evms-candidate-list/',admin_evms_candidate_list,name = 'admin_evms_candidate_list'),
    path('vendor-candidate-list/<int:id>/',admin_vendor_candidate_list,name = 'admin_vendor_candidate_list'),
    path('evms-candidate-profile/<int:id>/',evms_candidate_profile,name = 'evms_candidate_profile'),
    path('evms-vendor-candidate-profile/<int:id>/',evms_vendor_candidate_profile,name = 'evms_vendor_candidate_profile'),
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)