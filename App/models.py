from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, time, datetime
import pytz
from django.utils.timezone import now, timezone
from django.contrib.auth import get_user_model
from django.utils import timezone


# Helper function to get current user
def get_current_user():
    return get_user_model().objects.get(username='admin').id  # Default fallback user

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
    salary_ammount = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='employee_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='employee_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
class Employee_address(models.Model):
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='employee_address')
    permanent_address = models.CharField(max_length=100, null=True, blank=True)
    present_address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=100, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='employee_address_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='employee_address_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)


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
    created_by = models.ForeignKey(User, related_name='employee_additional_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='employee_additional_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Additional Info for {self.employee.first_name} {self.employee.last_name}"
    
class Family_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='family_member')
    member_name = models.CharField(max_length=100, blank=True)
    relation = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=100, blank=True)
    date_of_birth = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, related_name='family_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='family_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)
    
class Education_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='education_details')
    cource_name = models.CharField(max_length=200, blank=True)
    institution_name = models.CharField(max_length=200, blank=True)
    start_year = models.CharField(max_length=200, blank=True)
    end_year = models.CharField(max_length=200, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    description = models.CharField(max_length=200, blank=True)
    education_certificate = models.FileField(upload_to='Education-Certificate/', null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='education_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='education_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    
class EmployeeBankDetails(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bank_details')
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    confirm_account_number = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=11)
    created_by = models.ForeignKey(User, related_name='bank_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='bank_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

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
    created_by = models.ForeignKey(User, related_name='experience_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='experience_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    
class Documents_details(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents_details')
    document_number = models.CharField(max_length=200, blank=True)
    document_type = models.CharField(max_length=200, blank=True)
    other_document_type = models.CharField(max_length=255, blank=True, null=True)
    document_file = models.FileField(upload_to='Employee-Documents/', null=True)
    created_by = models.ForeignKey(User, related_name='documents_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='documents_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    

# Define IST timezone globally
IST = pytz.timezone('Asia/Kolkata')

class EmployeeSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    punch_in_time = models.DateTimeField(null=True, blank=True)  # Store login time in IST
    punch_out_time = models.DateTimeField(null=True, blank=True)  # Store logout time in IST
    total_time = models.DurationField(default=timedelta(0), null=True, blank=True)
    last_activity = models.DateTimeField(default=now)
    punch_out_reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, related_name='employee_session_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='employee_session_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    

class Meeting(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name='meeting_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='meeting_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    
class Designation(models.Model):
    name = models.CharField(max_length=100)  
    department = models.CharField(max_length=100)  # Department selection
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='designation_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='designation_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

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
    created_by = models.ForeignKey(User, related_name='attendance_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='attendance_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

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
    created_by = models.ForeignKey(User, related_name='monthly_attendance_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='monthly_attendance_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

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
    created_by = models.ForeignKey(User, related_name='leave_request_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='leave_request_updated', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.username}'s Leave Request from {self.start_date} to {self.end_date}"
    
    
class Holiday(models.Model):
    date = models.DateField()
    day = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, related_name='holiday_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='holiday_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_day_display()}) on {self.date}"
    
class Salary(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.CharField(max_length=100, blank=True, null=True)  
    year = models.TextField(blank=True, null=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    da = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Dearness Allowance
    ta = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Transport Allowance
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    pf = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Provident Fund
    esi = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # ESI
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Tax Deducted at Source
    leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='salary_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='salary_updated', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.month}/{self.year} - {self.get_status_display()}"

    @property
    def total_earnings(self):
        return (self.basic_salary + self.hra + self.da + self.ta + 
                self.medical_allowance + self.special_allowance + 
                self.bonus + self.other_earnings)

    @property
    def total_deductions(self):
        return (self.pf + self.esi + self.professional_tax + 
                self.tds + self.leave_deduction + self.other_deductions)

    @property
    def net_pay(self):
        return self.total_earnings - self.total_deductions
    
class OfficeExpense(models.Model):
    employee_name = models.CharField(max_length=100)
    item_name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_status = models.CharField(max_length=20,  default='Unpaid')
    description = models.CharField(max_length=255, blank=True)
    attech = models.FileField(upload_to='office_expense_attachments/', null=True)
    created_by = models.ForeignKey(User, related_name='office_expense_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='office_expense_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_name} - {self.employee_name}"
    
class MonthlyExpense(models.Model):
    month = models.DateField(unique=True)  # Stores the month (e.g., 2024-12-01)
    total_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Default set to 0
    created_by = models.ForeignKey(User, related_name='monthly_expense_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='monthly_expense_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.month.strftime('%B %Y')}: {self.total_expense}"
        
class Incentive(models.Model):
    employee_name = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='incentive_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='incentive_updated', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)
    
class Bonus(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='bonus_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='bonus_updated', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.amount} for {self.employee.name}'
    
class Resignation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, )
    resignation_date = models.DateField()
    last_working_day = models.DateField()
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name='resignation_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='resignation_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Resignation"
    
class Promotion(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    old_designation = models.CharField(max_length=100)
    new_designation = models.CharField(max_length=100)
    promotion_date = models.DateField()
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name='promotion_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='promotion_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.promotion_title}"
     
class Termination(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    termination_type = models.CharField(max_length=100)
    notice_date = models.DateField()
    termination_date = models.DateField()
    description = models.TextField()
    status = models.CharField(max_length=20, default='Pending')
    created_by = models.ForeignKey(User, related_name='termination_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='termination_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Termination of {self.employee} ({self.termination_type})"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    announcements_image = models.FileField(upload_to='Announcement-image/')
    created_by = models.ForeignKey(User, related_name='announcement_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='announcement_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # User who will receive the notification
    notification_type = models.CharField(max_length=200)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='notification_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='notification_updated', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.notification_type} - {self.message}"
    
class Award(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    award_type = models.CharField(max_length=255)
    award_date = models.DateField()
    gift = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name='award_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='award_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Award for {self.employee.name} - {self.award_type}"
    
class OfficeActivity(models.Model):
    title = models.CharField(max_length=255)
    activity_type = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    start_date = models.DateField()
    deadline = models.DateField()
    created_by = models.ForeignKey(User, related_name='office_activity_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='office_activity_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
class Warning(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    warning_date = models.DateField()
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name='warning_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='warning_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} - {self.subject}"

class Task(models.Model):
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=50)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='Pending')
    created_by = models.ForeignKey(User, related_name='task_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='task_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Candidate_registration(models.Model):
    employee_name = models.CharField(max_length=50)
    employee_assigned = models.CharField(max_length=50)
    register_time = models.DateTimeField(default=now)
    candidate_name = models.CharField(max_length=255)
    unique_code = models.CharField(max_length=255)
    candidate_mobile_number = models.CharField(max_length=15)
    candidate_alternate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_email_address = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    lead_source = models.CharField(max_length=255)
    preferred_state = models.CharField(max_length=255, blank=True, null=True)
    preferred_location = models.CharField(max_length=255, blank=True, null=True)
    origin_location = models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    diploma = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    experience_year = models.CharField(max_length=255, blank=True, null=True)
    experience_month = models.CharField(max_length=255, blank=True, null=True)
    current_company = models.CharField(max_length=255, blank=True, null=True)
    current_working_status = models.CharField(max_length=50, blank=True, null=True)
    current_salary = models.CharField(max_length=10, blank=True, null=True)
    current_salary_type = models.CharField(max_length=51, blank=True, null=True)
    expected_salary = models.CharField(max_length=10, blank=True, null=True)
    expected_salary_type = models.CharField(max_length=51, blank=True, null=True)
    call_connection = models.CharField(max_length=255, blank=True, null=True)
    calling_remark = models.CharField(max_length=255, blank=True, null=True)
    lead_generate = models.CharField(max_length=255, blank=True, null=True)
    send_for_interview = models.CharField(max_length=255, blank=True, null=True)
    next_follow_up_date_time = models.DateTimeField(blank=True, null=True)
    candidate_photo = models.FileField(upload_to='candidate-photo/') 
    candidate_resume = models.FileField(upload_to='candidate-resume/')
    remark = models.CharField(max_length=255,blank=True, null=True)
    submit_by = models.CharField(max_length=100, blank=True, null=True)
    selection_status = models.CharField(max_length=10, default='Pending')
    company_name = models.CharField(max_length=10, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    offered_salary = models.CharField(max_length=255, blank=True, null=True)
    joining_status = models.CharField(max_length=10, blank=True, null=True)
    selection_date = models.DateField(blank=True, null=True)
    candidate_joining_date = models.DateField(blank=True, null=True)
    emta_commission = models.CharField(max_length=255, blank=True, null=True)
    payout_date = models.DateField(blank=True, null=True)
    selection_remark = models.CharField(max_length=255, blank=True, null=True)
    other_lead_source = models.CharField(max_length=255, blank=True, null=True)
    other_qualification = models.CharField(max_length=255, blank=True, null=True)
    other_working_status = models.CharField(max_length=255, blank=True, null=True)
    other_call_connection = models.CharField(max_length=255, blank=True, null=True)
    other_lead_generate = models.CharField(max_length=255, blank=True, null=True)
    other_interview_status = models.CharField(max_length=255, blank=True, null=True)
    other_selection_status = models.CharField(max_length=255, blank=True, null=True)
    other_origin_location = models.CharField(max_length=255, blank=True, null=True)
    invoice_status = models.CharField(max_length=255, blank=True, null=True)
    invoice_paid_status = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=255, blank=True, null=True)
    invoice_date = models.DateField(blank=True, null=True)
    invoice_amount = models.CharField(max_length=255, blank=True, null=True)
    invoice_remark = models.CharField(max_length=255, blank=True, null=True)
    invoice_attachment = models.FileField(upload_to='invoice_attachments/', null=True, blank=True)
    created_by = models.ForeignKey(Employee, related_name='candidate_registration_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(Employee, related_name='candidate_registration_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        if not self.pk:  # New record being created
            if user:
                self.created_by = user
            super().save(*args, **kwargs)
            # Create activity log for creation
            CandidateActivity.objects.create(
                candidate=self,
                employee=user,
                action='created',
                changes={'initial': 'Record created'}
            )
        else:
            # Existing record being updated
            old_record = Candidate_registration.objects.get(pk=self.pk)
            changes = {}
            
            # Compare each field to find changes
            for field in self._meta.fields:
                field_name = field.name
                old_value = getattr(old_record, field_name)
                new_value = getattr(self, field_name)
                
                if old_value != new_value and field_name not in ['updated_at', 'created_at']:
                    changes[field_name] = {
                        'old': str(old_value),
                        'new': str(new_value)
                    }
            
            if user:
                self.updated_by = user
            
            super().save(*args, **kwargs)
            
            # Only create activity log if there were changes
            if changes:
                CandidateActivity.objects.create(
                    candidate=self,
                    employee=user,
                    action='updated',
                    changes=changes
                )
            
class CandidateActivity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
    ]
    
    candidate = models.ForeignKey(Candidate_registration, on_delete=models.CASCADE, related_name='activities')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    changes = models.JSONField(default=dict)  # Stores field names and their old/new values
    remark = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Candidate Activities'

    def __str__(self):
        return f"{self.get_action_display()} by {self.employee} on {self.candidate}"

class Candidate_chat(models.Model):
    candidate = models.ForeignKey(Candidate_registration, on_delete=models.CASCADE, related_name='chats')
    chat_date = models.DateTimeField(auto_now_add=True)
    chat_message = models.TextField()
    employee_name = models.CharField(max_length=255)
    chat_type = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Note'),
        ('candidate', 'Candidate Communication'),
        ('client', 'Client Communication')
    ], default='internal')
    is_important = models.BooleanField(default=False)
    next_followup = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='candidate_chat_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='candidate_chat_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-chat_date']
        verbose_name = 'Candidate Chat'
        verbose_name_plural = 'Candidate Chats'

    def __str__(self):
        return f"Chat with {self.candidate.name} by {self.employee_name}"

    def get_chat_type_class(self):
        return {
            'internal': 'primary',
            'candidate': 'success',
            'client': 'pink'
        }.get(self.chat_type, 'secondary')
    
class Candidate_Interview(models.Model):
    INTERVIEW_STATUS = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
    ]
    
    INTERVIEW_MODE = [
        ('in_person', 'In-Person'),
        ('phone', 'Phone'),
        ('video', 'Video Call'),
        ('online_test', 'Online Test'),
        ('assessment', 'Assessment'),
        ('group_discussion', 'Group Discussion'),
        ('walk_in', 'Walk-In'),
        ('campus', 'Campus'),
        ('telephonic', 'Telephonic'),
        ('virtual', 'Virtual'),
        ('face_to_face', 'Face-to-Face'),
        ('on_site', 'On Site'),
        ('other', 'Other'),
    ]

    candidate = models.ForeignKey(Candidate_registration, on_delete=models.CASCADE, related_name='interviews')
    interview_date_time = models.DateTimeField(blank=True, null=True)
    company_name = models.CharField(max_length=255)
    job_position = models.CharField(max_length=255)
    interviewer_name = models.CharField(max_length=255, blank=True, null=True)
    interviewer_email = models.EmailField(blank=True, null=True)
    interviewer_phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS, default='scheduled')
    interview_mode = models.CharField(max_length=20, choices=INTERVIEW_MODE, default='in_person')
    location = models.TextField(blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField(blank=True, null=True, help_text="Rating out of 10")
    is_technical = models.BooleanField(default=False)
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=60)
    requirements = models.TextField(blank=True, null=True, help_text="Any special requirements")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attachment = models.FileField(upload_to='interview_docs/', blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='candidate_interview_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='candidate_interview_updated', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-interview_date_time']
        verbose_name = 'Candidate Interview'
        verbose_name_plural = 'Candidate Interviews'

    def get_interview_datetime(self):
        if self.interview_date_time:
            return self.interview_date_time
        return None

    
    def __str__(self):
        return f"{self.candidate.name} - {self.company_name} ({self.interview_date_time})"

    def get_interview_datetime(self):
        return self.interview_date_time

class Company_registration(models.Model):
    handled_by = models.CharField(max_length=50, blank=True, null=True)
    opened_by = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_address = models.CharField(max_length=255, blank=True, null=True)
    company_logo = models.FileField(upload_to='Company-Logo/', blank=True, null=True)
    company_location = models.CharField(max_length=255, blank=True, null=True)
    company_unique_code = models.CharField(max_length=255, blank=True, null=True)
    company_email_address = models.EmailField(blank=True, null=True)
    company_contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    company_contact_person_contact_details = models.CharField(max_length=255, blank=True, null=True)
    company_contact_person_designation = models.CharField(max_length=255, blank=True, null=True)
    interview_address = models.CharField(max_length=255, blank=True, null=True)
    status_of_proposal = models.CharField(max_length=100, blank=True, null=True)
    attech_proposal = models.FileField(upload_to='Company-Proposals/', blank=True, null=True)
    invoice_generation_date = models.CharField(max_length=10, blank=True, null=True)
    payout_date = models.CharField(max_length=10, blank=True, null=True)
    payment_condiation = models.CharField(max_length=255, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    state_code = models.CharField(max_length=10, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    remark = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='company_registration_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='company_registration_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        form_name = kwargs.pop('form_name', None)
        is_new = not self.pk
        
        if is_new:
            super().save(*args, **kwargs)
            CompanyActivity.objects.create(
                company=self,
                content_type='company',
                employee=user,
                action='created',
                changes={'initial': 'Company record created'},
                form_used=form_name
            )
        else:
            old_record = Company_registration.objects.get(pk=self.pk)
            changes = {}
            
            for field in self._meta.fields:
                field_name = field.name
                if field_name in ['updated_at', 'created_at']:
                    continue
                    
                old_value = getattr(old_record, field_name)
                new_value = getattr(self, field_name)
                
                if old_value != new_value:
                    changes[field_name] = {
                        'old': str(old_value) if old_value is not None else '',
                        'new': str(new_value) if new_value is not None else ''
                    }
            
            super().save(*args, **kwargs)
            
            if changes:
                CompanyActivity.objects.create(
                    company=self,
                    content_type='company',
                    employee=user,
                    action='updated',
                    changes=changes,
                    form_used=form_name,
                    remark=f"Updated via {form_name} form" if form_name else None
                )

class VacancyDetails(models.Model):
    # Existing fields
    company = models.ForeignKey(Company_registration, on_delete=models.CASCADE, related_name='vacancies')
    job_profile = models.CharField(max_length=255, blank=True, null=True)
    company_vacancy_unique_code = models.CharField(max_length=15)
    vacancy_opening_date = models.DateField(blank=True, null=True)
    vacancy_status = models.CharField(max_length=10, blank=True, null=True)
    payroll = models.CharField(max_length=255, blank=True, null=True)
    third_party_name = models.CharField(max_length=255, blank=True, null=True)
    job_opening_origin = models.CharField(max_length=255, blank=True, null=True)
    sector_type = models.CharField(max_length=255, blank=True, null=True)
    department_name = models.CharField(max_length=255, blank=True, null=True)
    fresher_status = models.CharField(max_length=50, blank=True, null=True)
    minimum_age = models.CharField(max_length=10, blank=True, null=True)
    maximum_age = models.CharField(max_length=10, blank=True, null=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    minimum_experience = models.CharField(max_length=255, blank=True, null=True)
    maximum_experience = models.CharField(max_length=255, blank=True, null=True)
    minimum_education_qualification = models.CharField(max_length=255, blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    minimum_salary_range = models.CharField(max_length=255,blank=True, null=True)
    maximum_salary_range = models.CharField(max_length=255,blank=True, null=True)
    vacancy_closing_date = models.DateField(blank=True, null=True)
    special_instruction = models.CharField(max_length=255, blank=True, null=True)
    company_usp = models.CharField(max_length=255,blank=True, null=True)
    status_of_incentive = models.CharField(max_length=255, blank=True, null=True)
    replacement_criteria_days = models.CharField(max_length=255, blank=True, null=True)
    replacement_criteria = models.CharField(max_length=255, blank=True, null=True)
    job_opening_origin_other = models.CharField(max_length=255, blank=True, null=True)
    interview_rounds = models.CharField(max_length=255, blank=True, null=True)
    working_shift = models.CharField(max_length=255, blank=True, null=True)
    working_shift_other = models.CharField(max_length=255, blank=True, null=True)
    cab_facility = models.CharField(max_length=255, blank=True, null=True)
    cab_facility_other = models.CharField(max_length=255, blank=True, null=True)
    no_of_vacancies = models.CharField(max_length=255, blank=True, null=True)
    batch_date = models.CharField(max_length=255, blank=True, null=True)
    lingual_proficiency = models.CharField(max_length=255, blank=True, null=True)
    incentive_details = models.TextField(blank=True, null=True)
    minimum_salary_type = models.CharField(max_length=50, blank=True, null=True)
    maximum_salary_type = models.CharField(max_length=50, blank=True, null=True)
    
    # New payment-related fields
    PAYMENT_MODE_CHOICES = [
        ('Company Pay', 'Company Pay'),
        ('Salary Deduction', 'Salary Deduction'),
        ('SPDC/Candidate Pay', 'SPDC/Candidate Pay'),
    ]
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODE_CHOICES, blank=True, null=True)
    
    # Company Pay fields
    COMPANY_PAY_TYPE_CHOICES = [
        ('Flat', 'Flat'),
        ('Percentage of CTC', 'Percentage of CTC'),
        ('Pay as per days', 'Pay as per days'),
    ]
    company_pay_type = models.CharField(max_length=50, choices=COMPANY_PAY_TYPE_CHOICES, blank=True, null=True)
    flat_amount = models.CharField(max_length=255, blank=True, null=True)
    percentage_of_ctc = models.CharField(max_length=100, blank=True, null=True)
    pay_per_days = models.CharField(max_length=100, blank=True, null=True)
    
    # Salary Deduction fields
    salary_transfer_date = models.DateField(blank=True, null=True)
    expected_payment_date = models.DateField(blank=True, null=True)
    
    # SPDC/Candidate Pay fields
    candidate_salary_transfer_date = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='vacancy_details_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='vacancy_details_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        form_name = kwargs.pop('form_name', None)
        is_new = not self.pk
        
        if is_new:
            super().save(*args, **kwargs)
            CompanyActivity.objects.create(
                vacancy=self,
                content_type='vacancy',
                employee=user,
                action='created',
                changes={'initial': 'Vacancy record created'},
                form_used=form_name
            )
        else:
            old_record = VacancyDetails.objects.get(pk=self.pk)
            changes = {}
            
            for field in self._meta.fields:
                field_name = field.name
                if field_name in ['updated_at', 'created_at']:
                    continue
                    
                old_value = getattr(old_record, field_name)
                new_value = getattr(self, field_name)
                
                if old_value != new_value:
                    changes[field_name] = {
                        'old': str(old_value) if old_value is not None else '',
                        'new': str(new_value) if new_value is not None else ''
                    }
            
            super().save(*args, **kwargs)
            
            if changes:
                CompanyActivity.objects.create(
                    vacancy=self,
                    content_type='vacancy',
                    employee=user,
                    action='updated',
                    changes=changes,
                    form_used=form_name,
                    remark=f"Updated via {form_name} form" if form_name else None
                )
    
class CompanyActivity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('company', 'Company'),
        ('vacancy', 'Vacancy'),
    ]
    
    # Generic foreign key approach
    company = models.ForeignKey(
        Company_registration, 
        on_delete=models.CASCADE, 
        related_name='activities',
        null=True,
        blank=True
    )
    vacancy = models.ForeignKey(
        VacancyDetails,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True
    )
    
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        help_text="Type of object being tracked"
    )
    
    employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_activities'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    changes = models.JSONField(default=dict)
    remark = models.TextField(blank=True, null=True)
    form_used = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Which form was used to make this change"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Company Activities'

    def __str__(self):
        target = self.get_target()
        return f"{self.get_action_display()} by {self.employee or 'System'} on {target}"

    def get_target(self):
        if self.content_type == 'company' and self.company:
            return self.company.company_name
        elif self.content_type == 'vacancy' and self.vacancy:
            return f"{self.vacancy.job_profile} at {self.vacancy.company.company_name}"
        return "Unknown Target"
    
    def get_employee(self):
        """Get the Employee profile associated with this activity's user"""
        if hasattr(self.employee, 'employee'):
            return self.employee.employee
        return None
    
class Company_spoke_person(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('left', 'Left Company'),
    ]
    
    company = models.ForeignKey(Company_registration, on_delete=models.CASCADE, related_name='spoke_persons')
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True)
    last_contact_date = models.DateField(blank=True, null=True)
    next_followup = models.DateField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='company_spoke_person_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='company_spoke_person_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Company Contact Person"
        verbose_name_plural = "Company Contact Persons"
        ordering = ['-is_primary', '-priority', 'name']

    def __str__(self):
        return f"{self.name} ({self.designation})"
    
    # @property
    # def is_followup_due(self):
    #     return self.next_followup and self.next_followup <= timezone.now().date()
    
    
class company_communication(models.Model):
    COMMUNICATION_TYPES = [
        ('email', 'Email'),
        ('call', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('message', 'Message'),
        ('video_call', 'Video Call'),
        ('letter', 'Letter'),
        ('proposal', 'Proposal'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    company = models.ForeignKey(Company_registration, on_delete=models.CASCADE, related_name='communications')
    contact_person = models.CharField(max_length=255)
    designation = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    communication_date = models.DateTimeField()
    communication_type = models.CharField(max_length=50, choices=COMMUNICATION_TYPES)
    subject = models.CharField(max_length=255)
    communication_details = models.TextField()
    follow_up_date = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    outcome = models.TextField(blank=True, null=True)
    employee_name = models.CharField(max_length=255)
    attachment = models.FileField(upload_to='communication_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name='company_communication_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='company_communication_updated', on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-communication_date']
        verbose_name = 'Company Communication'
        verbose_name_plural = 'Company Communications'

    def __str__(self):
        return f"{self.communication_type} with {self.company.company_name} - {self.subject}"

    # @property
    # def is_follow_up_due(self):
    #     if self.follow_up_date:
    #         return self.follow_up_date <= timezone.now().date()
    #     return False
   

class Ticket(models.Model):
    TICKET_STATUS = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
        ('Reopened', 'Reopened'),
    ]
    
    TICKET_PRIORITY = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    TICKET_CATEGORY = [
        ('IT', 'IT'),
        ('HR', 'HR'),
        ('Finance', 'Finance'),
        ('Operations', 'Operations'),
        ('Facilities', 'Facilities'),
        ('Other', 'Other'),
    ]
    
    ticket_number = models.CharField(max_length=50, unique=True)
    ticket_name = models.CharField(max_length=255)
    ticket_description = models.TextField(blank=True, null=True)
    ticket_status = models.CharField(
        max_length=20,
        choices=TICKET_STATUS,
        default='Open'
    )
    ticket_priority = models.CharField(
        max_length=20,
        choices=TICKET_PRIORITY,
        default='Medium'
    )
    ticket_category = models.CharField(
        max_length=20,
        choices=TICKET_CATEGORY,
        default='Other'
    )
    ticket_assign_to = models.ForeignKey(Employee, related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    ticket_assign_by = models.ForeignKey(Employee, related_name='created_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    ticket_created_date = models.DateTimeField(auto_now_add=True)
    ticket_updated_date = models.DateTimeField(auto_now=True)
    ticket_closed_date = models.DateTimeField(blank=True, null=True)
    ticket_remark = models.TextField(blank=True, null=True)
    ticket_attachment = models.FileField(upload_to='ticket_attachments/', blank=True, null=True)
    ticket_due_date = models.DateTimeField(blank=True, null=True)
    ticket_sla = models.CharField(max_length=50, blank=True, null=True)
    ticket_related_to = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='ticket_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='ticket_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number if not provided
            last_ticket = Ticket.objects.order_by('-id').first()
            last_id = last_ticket.id if last_ticket else 0
            self.ticket_number = f"TKT-{last_id + 1:05d}"
            
        user = kwargs.pop('user', None)
        if user and not self.pk:
            self.created_by = user
        if user:
            self.updated_by = user
            
        # Set closed date if status is changed to Closed
        if self.pk:
            old_status = Ticket.objects.get(pk=self.pk).ticket_status
            if old_status != 'Closed' and self.ticket_status == 'Closed':
                self.ticket_closed_date = timezone.now()
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.ticket_name}"

    def get_status_color(self):
        status_colors = {
            'Open': 'primary',
            'In Progress': 'info',
            'Resolved': 'success',
            'Closed': 'secondary',
            'Reopened': 'warning',
        }
        return status_colors.get(self.ticket_status, 'light')

    def get_priority_color(self):
        priority_colors = {
            'Low': 'success',
            'Medium': 'info',
            'High': 'warning',
            'Critical': 'danger',
        }
        return priority_colors.get(self.ticket_priority, 'light')
    
class TicketActivity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('commented', 'Commented'),
        ('closed', 'Closed'),
        ('reopened', 'Reopened'),
    ]
    
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Ticket Activities'

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} on {self.ticket}"

    def save(self, *args, **kwargs):
        # Ensure timestamp is set on creation
        if not self.pk:
            self.timestamp = timezone.now()
        super().save(*args, **kwargs)
    
    
class Document(models.Model):
    DOCUMENT_TYPES = (
        ('private', 'Private'),
        ('public', 'Public'),
        ('hidden', 'Hidden'),
        ('ese_hi', 'Ese Hi'),
    )
    
    file_name = models.CharField(max_length=255)
    document = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES, default='private')
    role = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, related_name='created_documents', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, related_name='updated_documents', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name