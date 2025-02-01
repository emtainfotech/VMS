from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',custom_admin_login,name = 'custom_admin_login'),
    path('admin-signup/',admin_signup_view,name = 'admin_signup_view'),
    path('notifications/mark-as-read/', mark_notifications_as_read, name='mark_notifications_as_read'),
    path('Dashboard/',home,name = 'dashboard'),
    path('employee/',employee_view,name = 'employee_view'),
    path('employee-details/<int:id>/',employee_details_view,name = 'employee_details_view'),
    path('employee-details/<int:id>/', employee_details_view, name='employee-details'),
    path('admin-candidate-registration/',admin_candidate_registration,name = 'admin_candidate_registration'),
    path('candidate-list/',admin_candidate_list,name = 'admin_candidate_list'),
    path('candidate-details/<int:id>/', admin_candidate_profile, name='candidate-details'),
    path('designation/',designation_view,name = 'designation_view'),
    # path('designation/delete/<int:id>/', delete_designation, name='delete-designation'),
    # path('employee-attendence/',attendence_view,name = 'attendence_view'),
    path('leave-request/',leave_request_view,name = 'leave_request_view'),
    path('holiday/',holiday_view,name = 'holiday_view'),
    path('projects/',project_view,name = 'project_view'),
    path('Pay-List/',pay_list_view,name = 'pay_list_view'),
    path('update-salary-status/<int:salary_id>/', update_salary_status, name='update_salary_status'),
    path('delete-salary/<int:id>/', delete_salary, name='delete_salary'),
    path('Pay-Slip/',pay_slip_view,name = 'pay_payslip_view'),
    path('salary-slip/<int:salary_id>/', pay_slip_view, name='salary_slip'),
    path('office-expense/',office_expense_view,name = 'office_expense_view'),
    path('update-expense-status/<int:expense_id>/', update_expense_status, name='update_expense_status'),
    path('delete-expense/<int:id>/', delete_expense, name='delete_expense'),
    path('incentive/',incentive_view,name = 'incentive_view'),
    path('delete_incentive/<int:incentive_id>/', delete_incentive, name='delete_incentive'),
    path('update-incentive-status/<int:incentive_id>/', update_incentive_status, name='update_incentive_status'),
    path('bonus/',bonus_view,name = 'bonus_view'),
    path('update_bonus_status/<int:bonus_id>/', update_bonus_status, name='update_bonus_status'),
    path('delete_bonus/<int:bonus_id>/', delete_bonus, name='delete_bonus'),
    path('resignation/',resignation_view,name = 'resignation_view'),
    path('update-resignation/<int:resignation_id>/', update_resignation_status, name='update_resignation_status'),
    path('documents/',documents_view,name = 'documents_view'),
    path('promotion/',promotion_view,name = 'promotion_view'),
    path('delete-promotion/<int:promotion_id>/', delete_promotion, name='delete_promotion'),
    path('termination/',termination_view,name = 'termination_view'),
    path('delete-termination/<int:termination_id>/', delete_termination, name='delete_termination'),
    path('announcement/',announcement_view,name = 'announcement_view'),
    path('delete-announcement/<int:announcement_id>/', delete_announcement, name='delete_announcement'),
    path('team-meeting/',team_meeting_view,name = 'team_meeting_view'),
    path('delete-meeting/<int:meeting_id>/', delete_meeting, name='delete_meeting'),
    path('awards/',awards_view,name = 'awards_view'),
    path('delete-award/<int:award_id>/', delete_award, name='delete_award'),
    path('office-activities/',office_activity_view,name = 'office_activity_view'),
    path('delete-activity/<int:officeactivity_id>/', delete_activity, name='delete_activity'),
    path('clients/',clients_view,name = 'clients_view'),
    path('warning/',warning_view,name = 'warning_view'),
    path('delete-warning/<int:warning_id>/', delete_warning, name='delete_warning'),
    path('update-leave-status/<int:leave_id>/', update_leave_status, name='update_leave_status'),
    path('employee-attendence_details/<int:user_id>/', employee_attendence_details, name='employee_attendence_details'),
    path('admin-company-list/',admin_company_list,name = 'admin_company_list'),
    path('admin-company-registration/',admin_company_registration,name = 'admin_company_registration'),
    path('admin-company-profile/<int:id>/', admin_company_profile, name='admin_company_profile'),
    path('admin-vendor-list/',admin_vendor_list,name = 'admin_vendor_list'),
    path('evms-candidate-list/',admin_evms_candidate_list,name = 'admin_evms_candidate_list'),
    path('vendor-candidate-list/<int:id>/',admin_vendor_candidate_list,name = 'admin_vendor_candidate_list'),
    path('evms-candidate-profile/<int:id>/',evms_candidate_profile,name = 'evms_candidate_profile'),
    path('evms-vendor-candidate-profile/<int:id>/',evms_vendor_candidate_profile,name = 'evms_vendor_candidate_profile'),
    path("download-attendance/<int:user_id>/", download_attendance_excel, name="download_attendance_excel"),
    
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)