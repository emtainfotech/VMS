from django.contrib import admin
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('',custom_admin_login,name = 'custom_admin_login'),
    path('login/',custom_admin_login,name = 'custom_admin_login'),
    path("admin-logout/", custom_admin_logout, name="custom_admin_logout"),
    path('admin-signup/',admin_signup_view,name = 'admin_signup_view'),
    path('notifications/mark-as-read/', mark_notifications_as_read, name='mark_notifications_as_read'),
    path('Dashboard/',home,name = 'dashboard'),
    path('employee/',employee_view,name = 'employee_view'),
    path('employee-details/<int:id>/',employee_details_view,name = 'employee_details_view'),
    path('employee-details/<int:id>/', employee_details_view, name='employee-details'),
    path('designations/', designation_view, name='designation_view'),
    path('designations/edit/<int:designation_id>/', edit_designation, name='edit_designation'),
    path('designations/delete/<int:id>/', delete_designation, name='delete_designation'),
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
    path('expense/edit/<int:id>/', edit_expense, name='edit_expense'),
    path('expense/delete/<int:id>/', delete_expense, name='delete_expense'),
    path('incentive/',incentive_view,name = 'incentive_view'),
    path('delete_incentive/<int:incentive_id>/', delete_incentive, name='delete_incentive'),
    path('update-incentive-status/<int:incentive_id>/', update_incentive_status, name='update_incentive_status'),
    path('bonus/',bonus_view,name = 'bonus_view'),
    path('bonus/edit/<int:bonus_id>/', edit_bonus, name='edit_bonus'),
    path('bonus/delete/<int:bonus_id>/', delete_bonus, name='delete_bonus'),
    path('bonus/update-status/<int:bonus_id>/', update_bonus_status, name='update_bonus_status'),
    path('resignation/',resignation_view,name = 'resignation_view'),
    path('update-resignation/<int:resignation_id>/', update_resignation_status, name='update_resignation_status'),
    path('documents/',document_list, name='document_list'),
    path('documents/add/',add_document, name='add_document'),
    path('documents/edit/<int:document_id>/',edit_document, name='edit_document'),
    path('documents/delete/<int:document_id>/',delete_document, name='delete_document'),
    path('promotion/',promotion_view,name = 'promotion_view'),
    path('delete-promotion/<int:promotion_id>/', delete_promotion, name='delete_promotion'),
    path('terminations/', termination_view, name='termination_view'),
    path('terminations/edit/<int:termination_id>/', edit_termination, name='edit_termination'),
    path('terminations/delete/<int:termination_id>/', delete_termination, name='delete_termination'),
    path('announcement/',announcement_view,name = 'announcement_view'),
    path('meeting/', team_meeting_view, name='team_meeting_view'),
    path('meeting/edit/<int:meeting_id>/', edit_meeting, name='edit_meeting'),
    path('meeting/delete/<int:meeting_id>/', delete_meeting, name='delete_meeting'),
    path('awards/',awards_view,name = 'awards_view'),
    path('office-activities/',office_activity_view,name = 'office_activity_view'),
    path('delete-activity/<int:officeactivity_id>/', delete_activity, name='delete_activity'),
    path('clients/',clients_view,name = 'clients_view'),
    path('warning/',warning_view,name = 'warning_view'),
    path('delete-warning/<int:warning_id>/', delete_warning, name='delete_warning'),
    path('update-leave-status/<int:leave_id>/', update_leave_status, name='update_leave_status'),
    path('employee-attendence_details/<int:user_id>/', employee_attendence_details, name='employee_attendence_details'),
    path("download-attendance/<int:user_id>/", download_attendance_excel, name="download_attendance_excel"),
    path('department-employee-count/', department_employee_count, name='department_employee_count'),
    path('get-session-details/', get_session_details, name='get_session_details'),
    path('attendance-status/', today_employee_attendance_status, name='today_employee_attendance_status'),
    path('employee-attendance-list/', employee_attendance_list, name='employee_attendance_list'),
    path('tasks/assign/', assign_task, name='assign_task'),
    path('tasks/edit/<int:task_id>/', edit_task, name='edit_task'),
    path('tasks/delete/<int:task_id>/', delete_task, name='delete_task'),
    path('tasks/update-status/<int:task_id>/', update_task_status, name='update_task_status'),
    path('admin-profile/<int:id>/', admin_profile, name='admin_profile'),
    path('tickets/', ticket_list, name='ticket_list'),
    path('tickets/add/', add_ticket, name='add_ticket'),
    path('tickets/edit/<int:ticket_id>/', edit_ticket, name='edit_ticket'),
    path('tickets/delete/<int:ticket_id>/', delete_ticket, name='delete_ticket'),
    path('tickets/view/<int:ticket_id>/', view_ticket, name='view_ticket'),
    path('hr/initiate/', hr_initiate_onboarding, name='hr_initiate'),
    path('hr/employee/<int:employee_id>/', hr_view_employee_details, name='hr_view_details'),
    
    # Employee URL
    path('onboarding/<uuid:token>/', employee_onboarding, name='employee_onboarding'),
    
    

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)