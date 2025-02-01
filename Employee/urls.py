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
    path('employee-holiday/',employee_holiday_view,name = 'employee_holiday_view'),
    path('office-employee-expense/',office_employee_expense_view,name = 'office_employee_expense_view'),
    path('employee/resignation/', employee_resignation_view, name='employee_resignation_view'),
    path('delete-resignation/<int:resignation_id>/', delete_employee_resignation_view, name='delete_employee_resignation_view'),
    path('task-assign/',assign_task,name = 'assign_task'),
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
    path('vendor-candidate-list/<int:id>/',employee_vendor_candidate_list,name = 'employee_vendor_candidate_list'),
    path('evms-candidate-profile/<int:id>/',evms_candidate_profile,name = 'evms_candidate_profile'),
    path('evms-vendor-candidate-profile/<int:id>/',evms_vendor_candidate_profile,name = 'evms_vendor_candidate_profile'),
    
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)