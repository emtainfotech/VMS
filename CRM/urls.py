from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',crm_admin_login,name = 'crm_admin_login'),
    path('admin-logout/', crm_admin_logout, name='crm_admin_logout'),
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
    path('admin-vacancy-list/',admin_vacancy_list,name = 'admin_vacancy_list'),
    path('admin-profile/<int:id>/', crm_admin_profile, name='crm_admin_profile'),
    path('candidates/bulk-upload/', admin_candidate_bulk_upload, name='admin_candidate_bulk_upload'),
    path('candidate/<int:candidate_id>/chats/', admin_candidate_chat_list, name='admin_candidate_chat_list'),
    path('candidate/chats/<int:pk>/delete/', admin_delete_chat, name='admin_delete_chat'),
    path('candidate/<int:candidate_id>/interviews/', admin_interview_list, name='admin_interview_list'),
    path('interview/<int:interview_id>/', admin_interview_detail, name='admin_interview_detail'),
    path('interview/<int:interview_id>/delete/', admin_delete_interview, name='admin_delete_interview'),
    path('company/<int:company_id>/communications/', admin_company_communication_list, name='admin_company_communication_list'),
    path('communication/<int:communication_id>/', admin_company_communication_detail, name='admin_company_communication_detail'),
    path('communication/<int:communication_id>/delete/', admin_delete_company_communication, name='admin_delete_company_communication'),
    path('company/<int:company_id>/contacts/', admin_company_contacts_list, name='admin_company_contacts_list'),
    path('company/<int:company_id>/contacts/add/', admin_company_contacts_list, name='admin_company_contact_create'),
    path('contacts/<int:contact_id>/', admin_company_contact_detail, name='admin_company_contact_detail'),
    path('contacts/<int:contact_id>/delete/', admin_delete_company_contact, name='admin_delete_company_contact'),
    path('download-candidates/', download_candidate_details, name='download_candidates'),
    path('vendor/bank-details/<str:vendor_code>/', vendor_bank_details, name='vendor_bank_details'),
    path('vendor/process-payment/<str:vendor_code>/', process_payment, name='process_payment'),
    path('evms-candidate-list/',admin_evms_candidate_list,name = 'admin_evms_candidate_list'),
    path('evms-candidate-profile/<int:id>/',evms_candidate_profile,name = 'evms_candidate_profile'),
    path('evms-candidate-chat-list/<int:candidate_id>/',admin_evms_candidate_chat_list,name = 'admin_evms_candidate_chat_list'),
    path('evms-candidate-chat-list/<int:pk>/delete/',admin_evms_delete_chat,name = 'admin_evms_delete_chat'),
    path('evms-candidate-interview-list/<int:candidate_id>/',admin_evms_interview_list,name = 'admin_evms_interview_list'),
    path('evms-candidate-interview-detail/<int:interview_id>/',admin_evms_interview_detail,name = 'admin_evms_interview_detail'),
    path('evms-candidate-interview-detail/<int:interview_id>/delete/',admin_evms_delete_interview,name = 'admin_evms_delete_interview'),
    
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)