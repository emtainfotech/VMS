from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',custom_admin_login,name = 'custom_admin_login'),
    path('admin-logout/', custom_admin_logout, name='custom_admin_logout'),
    path('crm-dashboard/',crm_dashboard,name = 'crm_dashboard'),
    path('admin-candidate-registration/',admin_candidate_registration,name = 'admin_candidate_registration'),
    path('candidate-list/',admin_candidate_list,name = 'admin_candidate_list'),
    path('candidate-details/<int:id>/', admin_candidate_profile, name='admin_candidate_profile'),
    path('admin-company-list/',admin_company_list,name = 'admin_company_list'),
    path('admin-company-registration/',admin_company_registration,name = 'admin_company_registration'),
    path('admin-company-profile/<int:id>/', admin_company_profile, name='admin_company_profile'),
    path('admin-vendor-list/',admin_vendor_list,name = 'admin_vendor_list'),
    path('evms-candidate-list/',admin_evms_candidate_list,name = 'admin_evms_candidate_list'),
    path('vendor-candidate-list/<int:id>/',admin_vendor_candidate_list,name = 'admin_vendor_candidate_list'),
    path('evms-candidate-profile/<int:id>/',evms_candidate_profile,name = 'evms_candidate_profile'),
    path('evms-vendor-profile/<int:id>/',admin_vendor_profile,name = 'admin_vendor_profile'),
    path('vendor-pay-list/',admin_evms_vendor_paylist, name = 'admin_evms_vendor_paylist'),
    path('vendor-transaction-history/',admin_evms_vendor_transaction_history, name = 'admin_evms_vendor_transaction_history'),
    path('export-vendors/', admin_export_vendors_to_excel, name='admin_export_vendors_to_excel'),
    path('selected-candidate-list/', selected_candidate, name='selected_candidate'),
    path('follow-up-candidate/',follow_up_candidate, name = 'follow_up_candidate'),
    path('leads/',generated_leads, name = 'generated_leads'),
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)