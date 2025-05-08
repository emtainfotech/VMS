from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, time, datetime
import pytz
from django.utils.timezone import now

# Create your models here.
class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15,blank=True)
    refer_code = models.CharField(max_length=10, unique=True)
    date_of_birth = models.TextField(max_length=10 , null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True,)
    profileVerification = models.CharField(max_length=50,default='Under Process')    
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

class Vendor_bussiness_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100, null=True, blank=True)
    shop_address = models.CharField(max_length=266, null=True, blank=True)
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
    
    
from django.db import models
from django.utils.timezone import now, timedelta

class Candidate(models.Model):
    refer_code = models.CharField(max_length=50, blank=True, null=True)
    register_time = models.DateTimeField(default=now)
    employee_name = models.CharField(max_length=50, blank=True, null=True)
    candidate_name = models.CharField(max_length=255, blank=True, null=True)
    unique_code = models.CharField(max_length=255, blank=True, null=True)
    candidate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_alternate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_email_address = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    lead_source = models.CharField(max_length=255,default='EVMS', blank=True, null=True)
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
    expected_salary = models.CharField(max_length=10, blank=True, null=True)
    call_connection = models.CharField(max_length=255, blank=True, null=True)
    calling_remark = models.CharField(max_length=255, blank=True, null=True)
    lead_generate = models.CharField(max_length=255, blank=True, null=True)
    send_for_interview = models.CharField(max_length=255, blank=True, null=True)
    next_follow_up_date = models.CharField(max_length=255,blank=True, null=True)
    candidate_photo = models.FileField(upload_to='candidate-photo/', blank=True, null=True)
    candidate_resume = models.FileField(upload_to='candidate-resume/', blank=True, null=True)
    remark = models.CharField(max_length=255,blank=True, null=True)
    submit_by = models.CharField(max_length=100, blank=True, null=True)
    selection_status = models.CharField(max_length=10, blank=True, null=True)
    company_name = models.CharField(max_length=10, blank=True, null=True)
    offered_salary = models.CharField(max_length=255, blank=True, null=True)
    selection_date = models.DateField(blank=True, null=True)
    candidate_joining_date = models.CharField(max_length=255, blank=True, null=True)
    emta_commission = models.CharField(max_length=255, blank=True, null=True)
    payout_date = models.CharField(max_length=255, blank=True, null=True)
    unique_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    
    vendor_commission = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    vendor_payout_date = models.DateField(blank=True, null=True, default=None)
    vendor_commission_status = models.CharField(max_length=255, blank=True, null=True)
    commission_generation_date = models.DateField(blank=True, null=True, default=None)
    vendor_payment_remark = models.CharField(max_length=255, blank=True, null=True)
    admin_status = models.CharField(max_length=255, blank=True, null=True)
    payment_done_by = models.CharField(max_length=255, blank=True, null=True)
    payment_done_by_date = models.DateField(null=True, blank=True)
    submit_recipt = models.FileField(upload_to='vendor-payout-recipt/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Check if candidate is older than 150 days
        if self.register_time and (now() - self.register_time) > timedelta(days=150):
            # Only clear refer_code if NOT (Selected AND commission status is pending/processing)
            if not (self.selection_status == 'Selected' and 
                   self.vendor_commission_status in ['Failed', 'In Process', 'Pending']):
                self.refer_code = None
        
        # Check for duplicate candidates (based on mobile number or email)
        if self.candidate_mobile_number or self.candidate_email_address:
            duplicates = Candidate.objects.exclude(pk=self.pk)
            
            if self.candidate_mobile_number:
                duplicates = duplicates.filter(candidate_mobile_number=self.candidate_mobile_number)
            if self.candidate_email_address:
                duplicates = duplicates.filter(candidate_email_address=self.candidate_email_address)
            
            duplicate = duplicates.first()
            
            if duplicate:
                # If duplicate exists and has a different refer_code, update to new vendor's code
                if self.refer_code and duplicate.refer_code != self.refer_code:
                    # Preserve refer_code if selection and commission conditions are met
                    if not (duplicate.selection_status == 'Selected' and 
                           duplicate.vendor_commission_status in ['Failed', 'In Process', 'Pending']):
                        duplicate.refer_code = self.refer_code
                        duplicate.save()
        
        # Generate unique ID if not exists
        if not self.unique_id:
            last_candidate = Candidate.objects.order_by('id').last()
            if last_candidate and last_candidate.unique_id:
                last_id_number = int(last_candidate.unique_id[6:])  # Extract the number part and convert to int
                new_id_number = last_id_number + 1
            else:
                new_id_number = 1
            self.unique_id = f"C{new_id_number:06d}"
            
        super().save(*args, **kwargs)
        
        
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
        
        