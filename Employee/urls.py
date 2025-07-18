from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('', employee_login, name='employee_login'),
    path('login/', employee_login, name='employee_login'),
    path('logout/', employee_logout, name='employee_logout'),
    path('dashboard/', employee_dashboard, name='employee_dashboard'),
    path('employee-profile/<int:id>/', employee_profile_view, name='employee_profile_view'),
    path('employee-Leave-request/', employee_leave_request_view, name='employee_leave_request_view'),
    path('leave/edit/<int:leave_id>/', edit_leave_request, name='edit_leave_request'),
    path('leave/delete/<int:leave_id>/',delete_leave_request, name='delete_leave_request'),
    path('employee-holiday/',employee_holiday_view,name = 'employee_holiday_view'),
    path('office-employee-expense/',office_employee_expense_view,name = 'office_employee_expense_view'),
    path('employee/resignation/', employee_resignation_view, name='employee_resignation_view'),
    path('resignation/edit/<int:resignation_id>/', edit_employee_resignation_view, name='edit_employee_resignation_view'),
    path('resignation/delete/<int:resignation_id>/', delete_employee_resignation_view, name='delete_employee_resignation_view'),
    path('update-task-status/<int:task_id>/', update_task_status, name='update_task_status'),
    path('employee-update-task-status/<int:task_id>/', employee_update_task_status, name='employee_update_task_status'),
    path('employee-candidate-list/',employee_candidate_list,name = 'employee_candidate_list'),
    path('employee-candidate-registration/',employee_candidate_registration,name = 'employee_candidate_registration'),
    path('employee-candidate-profile/<int:id>/',employee_candidate_profile,name = 'employee_candidate_profile'),
    path('employee-company-list/',employee_company_list,name = 'employee_company_list'),
    path('employee-company-registration/',employee_company_registration,name = 'employee_company_registration'),
    path('employee-company-profile/<int:id>/', employee_company_profile, name='employee_company_profile'),
    path('employee-vendor-list/',employee_vendor_list,name = 'employee_vendor_list'),
    path('evms-candidate-list/',employee_evms_candidate_list,name = 'employee_evms_candidate_list'),
    path('vendor-profile/<int:id>/',employee_vendor_candidate_list,name = 'employee_vendor_candidate_list'),
    path('evms-candidate-profile/<int:id>/',employee_evms_candidate_profile,name = 'employee_evms_candidate_profile'),
    path('evms-vendor-candidate-profile/<int:id>/',evms_vendor_candidate_profile,name = 'evms_vendor_candidate_profile'),
    path('punch-in/', punch_in, name='punch_in'),
    path('punch-out/', punch_out, name='punch_out'),  # Punch Out URL
    path('birthdays-anniversaries/', birthday_and_anniversary_today, name='birthdays_anniversaries'),
    path('same-designation-list-json/', same_designation_list_json, name='same_designation_list_json'),
    path('ticket-list/', ticket_view, name='ticket_view'),
    path('performance-dashboard/',employee_performance_dashboard, name = 'employee_performance_dashboard'),
    path('employee-today-call-performance/',employee_chart_data, name = 'employee_chart_data'),
    path('employee-chart-data/', overall_employee_chart_data, name='overall_employee_chart_data'),
    path('each-day/',each_employee_chart_data, name = 'each_employee_chart_data'),
    path('get-placement-data/',get_revenue_placement_data, name = 'get_revenue_placement_data'),
    path('leave-details/', employee_leave_details, name='employee_leave_details'),
    path('employee-leave-details/', employee_attendance_details, name='employee_attendance_details'),
    path('work-hours-summary/',work_hours_summary, name='work_hours_summary'),
    path('selected-candidate-list/', employee_selected_candidate, name='employee_selected_candidate'),
    path('follow-up-candidate/',employee_follow_up_candidate, name = 'employee_follow_up_candidate'),
    path('leads/',employee_generated_leads, name = 'employee_generated_leads'),
    path('vendor-pay-list/',evms_vendor_paylist, name = 'evms_vendor_paylist'),
    path('vendor-transaction-history/',evms_vendor_transaction_history, name = 'evms_vendor_transaction_history'),
    path('export-vendors/', export_vendors_to_excel, name='export_vendors'),
    path('api/companies/', search_companies, name='search_companies'),
    path('employee-vacancy-list/', employee_vacancy_list, name='employee_vacancy_list'),
    path('candidate/<int:candidate_id>/chats/', candidate_chat_list, name='candidate_chat_list'),
    path('candidate/chats/<int:pk>/delete/', delete_chat, name='delete_chat'),
    path('candidate/<int:candidate_id>/interviews/', interview_list, name='interview_list'),
    path('interview/<int:interview_id>/', interview_detail, name='interview_detail'),
    path('interview/<int:interview_id>/delete/', delete_interview, name='delete_interview'),
    path('company/<int:company_id>/communications/', company_communication_list, name='company_communication_list'),
    path('communication/<int:communication_id>/', company_communication_detail, name='company_communication_detail'),
    path('communication/<int:communication_id>/delete/', delete_company_communication, name='delete_company_communication'),
    path('company/<int:company_id>/contacts/', company_contacts_list, name='company_contacts_list'),
    path('company/<int:company_id>/contacts/add/', company_contacts_list, name='company_contact_create'),
    path('contacts/<int:contact_id>/', company_contact_detail, name='company_contact_detail'),
    path('contacts/<int:contact_id>/delete/', delete_company_contact, name='delete_company_contact'),
    path('evms/candidate/<int:candidate_id>/interviews/', employee_evms_interview_list, name='employee_evms_interview_list'),
    path('evms/interview/<int:interview_id>/', employee_evms_interview_detail, name='employee_evms_interview_detail'),
    path('evms/interview/<int:interview_id>/delete/', employee_evms_delete_interview, name='employee_evms_delete_interview'),
    path('evms/candidate/<int:candidate_id>/chats/', employee_evms_candidate_chat_list, name='employee_evms_candidate_chat_list'),
    path('evms/chat/<int:pk>/delete/', employee_evms_delete_chat, name='employee_evms_delete_chat'),
    path('employee-assignment/', employee_assign_candidate, name='employee_assign_candidate'),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)