from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
from datetime import timedelta, time, datetime
import pytz
from django.utils.timezone import now
from App.models import Employee  
from django.utils.timezone import now, timedelta
from django.utils import timezone

# Create your models here.
class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15,blank=True)
    refer_code = models.CharField(max_length=10, unique=True)
    date_of_birth = models.TextField(max_length=10 , null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True,)
    profileVerification = models.CharField(max_length=50,default='Under Process')
    verification_remark = models.CharField(max_length=255, blank=True, null=True)
    total_commission_received = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    vendor_profile_image = models.ImageField(upload_to='Vendor_profile_image/', null=True, blank=True,) 
    qr_code_plain = models.ImageField(upload_to='qr_codes_plain/', blank=True, null=True)  # Add this field
    

class Vendor_profile_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    address = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    adhar_card_number = models.CharField(max_length=15, null=True, blank=True)
    pan_card_number = models.CharField(max_length=15, null=True, blank=True)
    adhar_card_image = models.FileField(upload_to='adhar/', null=True, blank=True)
    pan_card_image = models.FileField(upload_to='pan/', null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    pin_code = models.CharField(max_length=10, null=True, blank=True)
    other_location = models.CharField(max_length=255, null=True, blank=True)

class Vendor_bussiness_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100, null=True, blank=True)
    shop_address = models.CharField(max_length=266, null=True, blank=True)
    shop_location = models.CharField(max_length=255, null=True, blank=True)
    shop_pin_code = models.CharField(max_length=10, null=True, blank=True)
    shop_other_location = models.CharField(max_length=255, null=True, blank=True)
    busness_type = models.CharField(max_length=100, null=True, blank=True)
    Gumasta_number = models.CharField(max_length=15, null=True, blank=True)
    gumasta_image = models.FileField(upload_to='Gumasata/', null=True, blank=True)
    gst_number = models.CharField(max_length=20, null=True, blank=True)
    gst_image = models.FileField(upload_to='GST/', null=True, blank=True) 
    Bpan_number = models.CharField(max_length=15, null=True, blank=True)
    Bpan_image = models.FileField(upload_to='Bussiness pan card/', null=True, blank=True)
    MSME_number = models.CharField(max_length=15, null=True, blank=True)
    MSME_image = models.FileField(upload_to='MSME/', null=True, blank=True)
    Contact_number = models.CharField(max_length=12, null=True, blank=True)
    Bphoto_outer = models.FileField(upload_to='Bussiness photo/outer', null=True, blank=True)
    Bphoto_inside = models.FileField(upload_to='Bussiness photo/inside', null=True, blank=True)
    Busness_email = models.EmailField(max_length=50, null=True, blank=True)
    VCname = models.CharField(max_length=50, null=True, blank=True)
    VCmobile = models.CharField(max_length=12, null=True, blank=True)
    VCaddress = models.CharField(max_length=150, null=True, blank=True)
    
class Vendor_bank_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    bank_document = models.FileField(upload_to='Bank/')
    account_type = models.CharField(max_length=100, null=True, blank=True)
    preffered_payout_date = models.CharField(max_length=10, null=True, blank=True)
    account_holder_name = models.CharField(max_length=50, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    ifs_code = models.CharField(max_length=20, null=True, blank=True)
    micr_code = models.CharField(max_length=20, null=True, blank=True)
    bank_name = models.CharField(max_length=20, null=True, blank=True)
    

class Candidate(models.Model):
    employee_name = models.CharField(max_length=50)
    employee_assigned = models.CharField(max_length=50)
    register_time = models.DateTimeField(default=now)
    refer_code = models.CharField(max_length=50, blank=True, null=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    unique_code = models.CharField(max_length=255, blank=True, null=True)
    candidate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_alternate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_email_address = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    lead_source = models.CharField(max_length=255,default='EVMS', blank=True, null=True)
    preferred_state = models.CharField(max_length=255, blank=True, null=True)
    preferred_location = models.CharField(max_length=255, blank=True, null=True)
    origin_location = models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    diploma = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=255, blank=True, null=True)
    job_type = models.CharField(max_length=255, blank=True, null=True)
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
    candidate_photo = models.FileField(upload_to='candidate-photo/', blank=True, null=True)
    candidate_resume = models.FileField(upload_to='candidate-resume/', blank=True, null=True)
    remark = models.CharField(max_length=255,blank=True, null=True)
    submit_by = models.CharField(max_length=100, blank=True, null=True)
    selection_status = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=10, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    offered_salary = models.CharField(max_length=255, blank=True, null=True)
    selection_date = models.DateField(blank=True, null=True)
    joining_status = models.CharField(max_length=10, default='Pending', blank=True, null=True)
    candidate_joining_date = models.CharField(max_length=255, blank=True, null=True)
    emta_commission = models.CharField(max_length=255, blank=True, null=True)
    payout_date = models.CharField(max_length=255, blank=True, null=True)
    unique_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    vendor_commission = models.CharField(max_length=255, blank=True, null=True)
    vendor_payout_date = models.DateField(blank=True, null=True, default=None)
    vendor_commission_status = models.CharField(max_length=255, blank=True, null=True)
    commission_generation_date = models.DateField(blank=True, null=True, default=None)
    vendor_payment_remark = models.CharField(max_length=255, blank=True, null=True)
    admin_status = models.CharField(max_length=255, blank=True, null=True)
    payment_done_by = models.CharField(max_length=255, blank=True, null=True)
    payment_done_by_date = models.DateField(null=True, blank=True)
    submit_recipt = models.FileField(upload_to='vendor-payout-recipt/', blank=True, null=True)
    selection_remark = models.CharField(max_length=255, blank=True, null=True)
    invoice_status = models.CharField(max_length=255, blank=True, null=True)
    invoice_paid_status = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=255, blank=True, null=True)
    invoice_date = models.DateField(blank=True, null=True)
    invoice_amount = models.CharField(max_length=255, blank=True, null=True)
    invoice_remark = models.CharField(max_length=255, blank=True, null=True)
    invoice_attachment = models.FileField(upload_to='invoice_attachments/', null=True, blank=True)
    other_lead_source = models.CharField(max_length=255, blank=True, null=True)
    other_qualification = models.CharField(max_length=255, blank=True, null=True)
    other_working_status = models.CharField(max_length=255, blank=True, null=True)
    other_call_connection = models.CharField(max_length=255, blank=True, null=True)
    other_lead_generate = models.CharField(max_length=255, blank=True, null=True)
    other_interview_status = models.CharField(max_length=255, blank=True, null=True)
    other_selection_status = models.CharField(max_length=255, blank=True, null=True)
    other_origin_location = models.CharField(max_length=255, blank=True, null=True)
    other_preferred_location = models.CharField(max_length=255, blank=True, null=True)
    other_sector = models.CharField(max_length=255, blank=True, null=True)
    other_department = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(Employee, related_name='evms_candidate_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(Employee, related_name='evms_candidate_updated', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        # Handle unique_id generation
        if not self.unique_id:
            with transaction.atomic():
                last_candidate = Candidate.objects.select_for_update().order_by('-id').first()
                if last_candidate and last_candidate.unique_id:
                    try:
                        last_id_number = int(last_candidate.unique_id[1:])
                    except ValueError:
                        last_id_number = 0
                else:
                    last_id_number = 0
                new_id_number = last_id_number + 1
                self.unique_id = f"C{new_id_number:06d}"

        # Handle refer_code logic for old candidates
        if self.register_time and (now() - self.register_time) > timedelta(days=150):
            if not (self.selection_status == 'Selected' and 
                   self.vendor_commission_status in ['Failed', 'In Process', 'Pending']):
                self.refer_code = None

        # Handle duplicate candidates
        if self.candidate_mobile_number or self.candidate_email_address:
            duplicates = Candidate.objects.exclude(pk=self.pk)
            
            if self.candidate_mobile_number:
                duplicates = duplicates.filter(candidate_mobile_number=self.candidate_mobile_number)
            if self.candidate_email_address:
                duplicates = duplicates.filter(candidate_email_address=self.candidate_email_address)
            
            duplicate = duplicates.first()
            
            if duplicate and self.refer_code and duplicate.refer_code != self.refer_code:
                if not (duplicate.selection_status == 'Selected' and 
                       duplicate.vendor_commission_status in ['Failed', 'In Process', 'Pending']):
                    duplicate.refer_code = self.refer_code
                    duplicate.save()

        # Handle activity logging
        if not self.pk:  # New record being created
            if user:
                self.created_by = user
            super().save(*args, **kwargs)
            # Create activity log for creation
            EVMS_CandidateActivity.objects.create(
                candidate=self,
                employee=user,
                action='created',
                changes={'initial': 'Record created'}
            )
        else:
            # Existing record being updated
            old_record = Candidate.objects.get(pk=self.pk)
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
                EVMS_CandidateActivity.objects.create(
                    candidate=self,
                    employee=user,
                    action='updated',
                    changes=changes
                )



class EVMS_CandidateActivity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='activities')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='evms_candidate_activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    changes = models.JSONField(default=dict)
    remark = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Candidate Activities'

    def __str__(self):
        return f"{self.get_action_display()} by {self.employee} on {self.candidate}"

class EVMS_Candidate_chat(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='chats')
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
    created_by = models.ForeignKey(User, related_name='evms_candidate_chat_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='evms_candidate_chat_updated', on_delete=models.SET_NULL, null=True, blank=True)
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
    
class EVMS_Candidate_Interview(models.Model):
    INTERVIEW_STATUS = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Rescheduled', 'Rescheduled'),
        ('Cancelled', 'Cancelled'),
        ('No Show', 'No Show'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
        ('On Hold', 'On Hold'),
        ('Pending', 'Pending'),
        ('In Process', 'In Process'),
        ('Failed', 'Failed'),
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

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='interviews')
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
    created_by = models.ForeignKey(User, related_name='evms_candidate_interview_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='evms_candidate_interview_updated', on_delete=models.SET_NULL, null=True, blank=True)

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


        
        
class Notification(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True)
    url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        
class Referal_poster(models.Model) :
    referal_image = models.FileField(upload_to='referal_poster/', null=True, blank=True)
        
        
# EMTA.co.in Job Application Model

from django.db import models
import os

# A function to define the upload path for resumes
def resume_upload_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/resumes/<email>_<filename>
    return os.path.join('resumes', f"{instance.email}_{filename}")

class JobApplication(models.Model):
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)
    phone = models.CharField(max_length=15)
    
    # Professional Information
    position_of_interest = models.CharField(max_length=255, blank=True, null=True, verbose_name="Position of Interest")
    previous_experience = models.TextField(verbose_name="Previous Work Experience")
    resume = models.FileField(upload_to=resume_upload_path, blank=True, null=True)
    portfolio_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Portfolio URL")
    
    # Logistics
    interview_availability = models.TextField()
    address = models.TextField(blank=True, null=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application from {self.first_name} {self.last_name} for {self.position_of_interest}"

    class Meta:
        ordering = ['-submitted_at']


class CourseInquiry(models.Model):
    COURSE_CHOICES = [
        ('Sales Officer', 'Sales Officer Training Program'),
        ('Relationship Manager', 'Relationship Manager Training Program'),
        ('Credit Officer', 'Credit Officer Training Program'),
        ('Operations Training', 'Operations Training Program'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    course_interest = models.CharField(max_length=100, choices=COURSE_CHOICES)
    address = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry from {self.first_name} {self.last_name} for {self.course_interest}"

    class Meta:
        ordering = ['-submitted_at']
        verbose_name_plural = "Course Inquiries"