from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

# Unregister the default User admin
admin.site.unregister(User)

# Custom User Admin with Employee inline
class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'Employee'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (EmployeeInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_employee_id')
    list_select_related = ('employee',)

    def get_employee_id(self, instance):
        return instance.employee.employee_id
    get_employee_id.short_description = 'Employee ID'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

admin.site.register(User, CustomUserAdmin)

# ModelAdmin classes for all your models
@admin.register(Employee_address)
class EmployeeAddressAdmin(admin.ModelAdmin):
    list_display = ('employee', 'city', 'state', 'country')
    search_fields = ('employee__first_name', 'employee__last_name', 'city', 'state')
    list_filter = ('state', 'country')

@admin.register(EmployeeAdditionalInfo)
class EmployeeAdditionalInfoAdmin(admin.ModelAdmin):
    list_display = ('employee', 'gender', 'date_of_birth', 'blood_group')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('gender', 'blood_group')

@admin.register(Family_details)
class FamilyDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'member_name', 'relation', 'contact_number')
    search_fields = ('employee__first_name', 'employee__last_name', 'member_name')
    list_filter = ('relation',)

@admin.register(Education_details)
class EducationDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'cource_name', 'institution_name', 'start_year', 'end_year')
    search_fields = ('employee__first_name', 'employee__last_name', 'institution_name')
    list_filter = ('cource_name',)

@admin.register(EmployeeBankDetails)
class EmployeeBankDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'bank_name', 'account_number', 'ifsc_code')
    search_fields = ('employee__first_name', 'employee__last_name', 'account_number')
    list_filter = ('bank_name',)

@admin.register(Experience_details)
class ExperienceDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'organization_name', 'designation_name', 'start_date', 'end_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'organization_name')
    list_filter = ('designation_name',)

@admin.register(Documents_details)
class DocumentsDetailsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_type', 'document_number')
    search_fields = ('employee__first_name', 'employee__last_name', 'document_number')
    list_filter = ('document_type',)

@admin.register(EmployeeSession)
class EmployeeSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'punch_in_time', 'punch_out_time', 'total_time')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('punch_in_time', 'punch_out_time')

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'time', 'location', 'department')
    search_fields = ('title', 'location', 'department')
    list_filter = ('date', 'department')

@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'color')
    search_fields = ('name', 'department')
    list_filter = ('department',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
    list_filter = ('date', 'status')

@admin.register(MonthlyAttendance)
class MonthlyAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'year', 'month', 'total_present', 'total_absent')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
    list_filter = ('year', 'month')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'status', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    list_filter = ('status', 'start_date', 'end_date')

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'day')
    search_fields = ('name', 'day')
    list_filter = ('date',)

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'basic_salary', 'net_pay', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('month', 'year', 'status')
    readonly_fields = ('total_earnings', 'total_deductions', 'net_pay')

@admin.register(OfficeExpense)
class OfficeExpenseAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'item_name', 'purchase_date', 'amount', 'paid_status')
    search_fields = ('employee_name', 'item_name')
    list_filter = ('purchase_date', 'paid_status')

@admin.register(MonthlyExpense)
class MonthlyExpenseAdmin(admin.ModelAdmin):
    list_display = ('month', 'total_expense')
    search_fields = ('month',)
    list_filter = ('month',)

@admin.register(Incentive)
class IncentiveAdmin(admin.ModelAdmin):
    list_display = ('employee_name', 'amount', 'status', 'created_at')
    search_fields = ('employee_name__first_name', 'employee_name__last_name', 'reason')
    list_filter = ('status', 'created_at')

@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'status', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    list_filter = ('status', 'created_at')

@admin.register(Resignation)
class ResignationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'resignation_date', 'last_working_day', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('status', 'resignation_date')

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'old_designation', 'new_designation', 'promotion_date')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('promotion_date',)

@admin.register(Termination)
class TerminationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'termination_type', 'termination_date', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')
    list_filter = ('termination_type', 'status')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date')
    search_fields = ('title', 'description')
    list_filter = ('start_date', 'end_date')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'message', 'is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_filter = ('notification_type', 'is_read')

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('employee', 'award_type', 'award_date', 'gift')
    search_fields = ('employee__first_name', 'employee__last_name', 'award_type')
    list_filter = ('award_type', 'award_date')

@admin.register(OfficeActivity)
class OfficeActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type', 'start_date', 'deadline')
    search_fields = ('title', 'activity_type')
    list_filter = ('activity_type', 'start_date')

@admin.register(Warning)
class WarningAdmin(admin.ModelAdmin):
    list_display = ('employee', 'subject', 'warning_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'subject')
    list_filter = ('warning_date',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'priority', 'due_date', 'status')
    search_fields = ('title', 'assigned_to__first_name', 'assigned_to__last_name')
    list_filter = ('priority', 'status', 'due_date')

@admin.register(Candidate_registration)
class CandidateRegistrationAdmin(admin.ModelAdmin):
    list_display = ('candidate_name', 'candidate_mobile_number', 'lead_source', 'current_working_status', 'selection_status')
    search_fields = ('candidate_name', 'candidate_mobile_number', 'lead_source')
    list_filter = ('lead_source', 'current_working_status', 'selection_status')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Candidate_chat)
class CandidateChatAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'chat_date', 'employee_name', 'chat_type')
    search_fields = ('candidate__candidate_name', 'employee_name')
    list_filter = ('chat_type', 'chat_date')

@admin.register(Candidate_Interview)
class CandidateInterviewAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'company_name', 'interview_date_time', 'status')
    search_fields = ('candidate__candidate_name', 'company_name')
    list_filter = ('status', 'interview_date_time', 'company_name')

@admin.register(Company_registration)
class CompanyRegistrationAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_location', 'company_email_address', 'status_of_proposal')
    search_fields = ('company_name', 'company_location')
    list_filter = ('status_of_proposal',)

@admin.register(VacancyDetails)
class VacancyDetailsAdmin(admin.ModelAdmin):
    list_display = ('company', 'job_profile', 'vacancy_status', 'vacancy_opening_date', 'vacancy_closing_date')
    search_fields = ('company__company_name', 'job_profile')
    list_filter = ('vacancy_status', 'vacancy_opening_date')

@admin.register(Company_spoke_person)
class CompanySpokePersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'designation', 'email', 'phone', 'is_primary')
    search_fields = ('name', 'company__company_name', 'email')
    list_filter = ('is_primary', 'status')

@admin.register(company_communication)
class CompanyCommunicationAdmin(admin.ModelAdmin):
    list_display = ('company', 'contact_person', 'communication_type', 'communication_date', 'priority')
    search_fields = ('company__company_name', 'contact_person')
    list_filter = ('communication_type', 'priority', 'communication_date')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'ticket_name', 'ticket_status', 'ticket_priority', 'ticket_created_date')
    search_fields = ('ticket_number', 'ticket_name')
    list_filter = ('ticket_status', 'ticket_priority', 'ticket_created_date')