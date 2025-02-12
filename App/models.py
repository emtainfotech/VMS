from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, time, datetime
import pytz
from django.utils.timezone import now

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)  
    employee_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    designation = models.CharField(max_length=100, null=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    joining_date = models.DateField()
    employee_photo = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
class Employee_address(models.Model) :
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='employee_address')
    permanent_address = models.CharField(max_length=100, null=True, blank=True)
    present_address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)


class EmployeeAdditionalInfo(models.Model):
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='additional_info')
    date_of_birth = models.DateField(null=True, blank=True)
    gender_choices = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=gender_choices)
    blood_group = models.CharField(max_length=100, null=True, blank=True)
    reporting_to = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Additional Info for {self.employee.first_name} {self.employee.last_name}"
    
class Family_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='family_member')
    member_name = models.CharField(max_length=100, blank=True)
    relation = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=100, blank=True)
    date_of_birth = models.CharField(max_length=100, blank=True)
    
class Education_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='education_details')
    cource_name = models.CharField(max_length=200, blank=True)
    institution_name = models.CharField(max_length=200, blank=True)
    start_year = models.CharField(max_length=200, blank=True)
    end_year = models.CharField(max_length=200, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=200, blank=True)
    education_certificate = models.FileField(upload_to='Education-Certificate/', null=True, blank=True)

    
class EmployeeBankDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bank_details')
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    confirm_account_number = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=11)

    def __str__(self):
        return f"Bank Details of {self.employee.first_name} {self.employee.last_name}"
    
class Experience_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='experience_details')
    organization_name = models.CharField(max_length=200, blank=True)
    designation_name = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=200, blank=True)
    experience_certificate = models.FileField(upload_to='Experience-Certificate/', null=True)

    
class Documents_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents_details')
    document_number = models.CharField(max_length=200, blank=True)
    document_type = models.CharField(max_length=200, blank=True)
    document_file = models.FileField(upload_to='Employee-Documents/', null=True)

    

# Define IST timezone globally
IST = pytz.timezone('Asia/Kolkata')

class EmployeeSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(null=True, blank=True)  # Store login time in IST
    logout_time = models.DateTimeField(null=True, blank=True)  # Store logout time in IST
    total_time = models.DurationField(default=timedelta(0), null=True, blank=True)
    last_activity = models.DateTimeField(default=now)
    logout_reason = models.CharField(max_length=255)

    def calculate_work_hours(self):
        if not self.logout_time:
            return timedelta(0)

        # Convert login and logout times to IST (this should already be in IST)
        login_ist = self.login_time
        logout_ist = self.logout_time

        # Define working hours in IST
        work_start = datetime.combine(login_ist.date(), time(10, 0), IST)
        work_end = datetime.combine(login_ist.date(), time(19, 30), IST)

        # Adjust login/logout times within working hours
        adjusted_login = max(login_ist, work_start)
        adjusted_logout = min(logout_ist, work_end)

        # Return zero timedelta if logout occurs before login
        if adjusted_logout < adjusted_login:
            return timedelta(0)

        return adjusted_logout - adjusted_login

    def save(self, *args, **kwargs):
        # Ensure times are saved in IST
        if not self.login_time:  # New session
            self.login_time = datetime.now(IST)  # Set login time in IST
        if self.logout_time is None:  # If logout_time is not set, don't update it
            self.logout_time = self.logout_time or None  # Optional: You can manually set this later
        if self.logout_time:  # If logout_time is set, calculate the total work time
            self.total_time = self.calculate_work_hours()
        super().save(*args, **kwargs)

    @property
    def login_time_ist(self):
        """ Returns login_time in IST (already saved in IST) """
        return self.login_time

    @property
    def logout_time_ist(self):
        """ Returns logout_time in IST (already saved in IST) """
        return self.logout_time


class Meeting(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    department = models.CharField(max_length=255)

    def __str__(self):
        return self.title
    
    
class Designation(models.Model):
    name = models.CharField(max_length=100)  
    department = models.CharField(max_length=100)  # Department selection

    def __str__(self):
        return self.name
    
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
        ('holiday', 'Holiday'),
        ('on_leave', 'On Leave'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')

    def __str__(self):
        return f"{self.employee.username} - {self.date} - {self.status}"
    
class MonthlyAttendance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    total_present = models.PositiveIntegerField(default=0)
    total_absent = models.PositiveIntegerField(default=0)
    total_half_day = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year}"
        
        
class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Employee who raised the leave request
    reason = models.TextField()
    attachment = models.FileField(upload_to='leave_attachments/')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.employee.username}'s Leave Request from {self.start_date} to {self.end_date}"
    
    
class Holiday(models.Model):
    date = models.DateField()
    day = models.CharField(max_length=15)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.get_day_display()}) on {self.date}"
    


from django.contrib.auth.models import User

class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    basic_salary = models.FloatField(default=0)
    dearness_allowance = models.FloatField(default=0)
    transport_allowance = models.FloatField(default=0)
    mobile_allowance = models.FloatField(default=0)
    bonus = models.FloatField(default=0)
    others_earning = models.FloatField(default=0)
    provident_fund = models.FloatField(default=0)
    security_deposit = models.FloatField(default=0)
    personal_loan = models.FloatField(default=0)
    early_leaving = models.FloatField(default=0)
    employee_type = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20)

    @property
    def total_earnings(self):
        return (
            self.basic_salary + self.dearness_allowance +
            self.transport_allowance + self.mobile_allowance +
            self.bonus + self.others_earning
        )

    @property
    def total_deductions(self):
        return (
            self.provident_fund + self.security_deposit +
            self.personal_loan + self.early_leaving
        )

    @property
    def net_salary(self):
        return self.total_earnings - self.total_deductions

    
class OfficeExpense(models.Model):
    employee_name = models.CharField(max_length=100)
    item_name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_status = models.CharField(max_length=20,  default='Unpaid')
    attech = models.FileField(upload_to='office_expense_attachments/', null=True)

    def __str__(self):
        return f"{self.item_name} - {self.employee_name}"
    
class MonthlyExpense(models.Model):
    month = models.DateField(unique=True)  # Stores the month (e.g., 2024-12-01)
    total_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default set to 0

    def __str__(self):
        return f"{self.month.strftime('%B %Y')}: {self.total_expense}"
    
    
from django.utils import timezone    
class Incentive(models.Model):
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(default=timezone.now)
    
class Bonus(models.Model):
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'{self.amount} for {self.employee.name}'
    


class Resignation(models.Model):

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, )
    resignation_date = models.DateField()
    last_working_day = models.DateField()
    description = models.TextField()

    def __str__(self):
        return f"{self.user.username} - Resignation"
    

class Promotion(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    old_designation = models.CharField(max_length=100)
    new_designation = models.CharField(max_length=100)
    promotion_date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return f"{self.employee} - {self.promotion_title}"
    
    
class Termination(models.Model):

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    termination_type = models.CharField(max_length=100)
    notice_date = models.DateField()
    termination_date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return f"Termination of {self.employee} ({self.termination_type})"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    announcements_image = models.FileField(upload_to='Announcement-image/')

    def __str__(self):
        return self.title
    

from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link notification to a specific employee
    notification_type = models.CharField(max_length=200)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.notification_type} - {self.message}"
    
class Award(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    award_type = models.CharField(max_length=255)
    award_date = models.DateField()
    gift = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return f"Award for {self.employee.name} - {self.award_type}"
    

class OfficeActivity(models.Model):
    title = models.CharField(max_length=255)
    activity_type = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    start_date = models.DateField()
    deadline = models.DateField()

    def __str__(self):
        return self.title
    
class Warning(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    warning_date = models.DateField()
    description = models.TextField()

    def __str__(self):
        return f"{self.employee.name} - {self.subject}"


class Task(models.Model):
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=50)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return self.title
    
    


class Candidate_registration(models.Model):
    employee_name = models.CharField(max_length=50)
    candidate_name = models.CharField(max_length=255)
    unique_code = models.CharField(max_length=255)
    candidate_mobile_number = models.CharField(max_length=15)
    candidate_alternate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_email_address = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10)
    lead_source = models.CharField(max_length=255)
    preferred_location = models.CharField(max_length=255, blank=True, null=True)
    origin_location = models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255)
    diploma = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    experience_year = models.IntegerField(blank=True, null=True)
    experience_month = models.IntegerField(blank=True, null=True)
    current_company = models.CharField(max_length=255, blank=True, null=True)
    current_working_status = models.CharField(max_length=50)
    current_salary = models.CharField(max_length=10, blank=True, null=True)
    expected_salary = models.CharField(max_length=10, blank=True, null=True)
    call_connection = models.CharField(max_length=255, blank=True, null=True)
    calling_remark = models.CharField(max_length=255, blank=True, null=True)
    lead_generate = models.CharField(max_length=255, blank=True, null=True)
    send_for_interview = models.CharField(max_length=255, blank=True, null=True)
    next_follow_up_date = models.CharField(max_length=255,blank=True, null=True)
    candidate_photo = models.FileField(upload_to='candidate-photo/')
    candidate_resume = models.FileField(upload_to='candidate-resume/')
    remark = models.CharField(max_length=255,blank=True, null=True)
    register_time = models.DateTimeField(default=now)
    submit_by = models.CharField(max_length=100)
    selection_status = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=10, blank=True, null=True)
    offered_salary = models.CharField(max_length=255, blank=True, null=True)
    selection_date = models.CharField(max_length=255, blank=True, null=True)
    candidate_joining_date = models.CharField(max_length=255, blank=True, null=True)
    emta_commission = models.CharField(max_length=255, blank=True, null=True)
    payout_date = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.candidate_name



class Company_registration(models.Model):
    employee_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=255)
    company_logo = models.FileField(upload_to='Company-Logo/')
    company_location = models.CharField(max_length=255)
    company_unique_code = models.CharField(max_length=255)
    job_profile = models.CharField(max_length=255, blank=True, null=True)
    company_vacancy_unique_code = models.CharField(max_length=15)
    vacancy_opening_date = models.CharField(max_length=255, blank=True, null=True)
    company_email_address = models.EmailField(blank=True, null=True)
    vacancy_status = models.CharField(max_length=10)
    company_contact_person_name = models.CharField(max_length=255)
    company_contact_person_contact_details = models.CharField(max_length=255, blank=True, null=True)
    company_contact_person_designation = models.CharField(max_length=255, blank=True, null=True)
    interview_address = models.CharField(max_length=255)
    payroll = models.CharField(max_length=255, blank=True, null=True)
    third_party_name = models.CharField(max_length=255, blank=True, null=True)
    job_opening_origin = models.CharField(max_length=255, blank=True, null=True)
    sector_type = models.CharField(max_length=255, blank=True, null=True)
    department_name = models.CharField(max_length=255, blank=True, null=True)
    fresher_status = models.CharField(max_length=50)
    minimum_age = models.CharField(max_length=10, blank=True, null=True)
    maximum_age = models.CharField(max_length=10, blank=True, null=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    minimum_experience = models.CharField(max_length=255, blank=True, null=True)
    maximum_experience = models.CharField(max_length=255, blank=True, null=True)
    minimum_education_qualification = models.CharField(max_length=255, blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    minimum_salary_range = models.CharField(max_length=255,blank=True, null=True)
    maximum_salary_range = models.CharField(max_length=255,blank=True, null=True)
    vacancy_closing_date = models.CharField(max_length=255, blank=True, null=True)
    special_instruction = models.CharField(max_length=255, blank=True, null=True)
    company_usp = models.CharField(max_length=255,blank=True, null=True)
    status_of_incentive = models.CharField(max_length=255, blank=True, null=True)
    status_of_proposal = models.CharField(max_length=100)
    invoice_generation_date = models.CharField(max_length=10, blank=True, null=True)
    payout_date = models.CharField(max_length=10, blank=True, null=True)
    payment_condiation = models.CharField(max_length=255, blank=True, null=True)
    replacement_criteria = models.CharField(max_length=255, blank=True, null=True)
    remark = models.CharField(max_length=255, blank=True, null=True)
   

    def __str__(self):
        return self.company_name
