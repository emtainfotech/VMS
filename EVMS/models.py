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
    date_of_birth = models.TextField(max_length=10)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True,)
    profileVerification = models.CharField(max_length=50,default='Under Process')    
    total_commission_received = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    vendor_profile_image = models.ImageField(upload_to='Vendor_profile_image/', null=True, blank=True,) 
    
    def get_or_create_profile_document(self):
        profile_document, created = ProfileDocument.objects.get_or_create(vendor=self)
        return profile_document
    def get_or_create_BussinessDetails(self):
        Bussiness_Details, created = BussinessDetails.objects.get_or_create(vendor=self)
        return Bussiness_Details
    def get_or_create_BankDetails(self):
        bank_details, created = Bank.objects.get_or_create(vendor=self)
        return bank_details
    
    
 
class Vendor_profile_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    address = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    adhar_card_number = models.CharField(max_length=15)
    pan_card_number = models.CharField(max_length=15)
    adhar_card_image = models.FileField(upload_to='adhar/')
    pan_card_image = models.FileField(upload_to='pan/')
    location = models.CharField(max_length=255)

class Vendor_bussiness_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    Gumasta_number = models.CharField(max_length=15)
    gumasta_image = models.FileField(upload_to='Gumasata/')
    gst_number = models.CharField(max_length=20)
    gst_image = models.FileField(upload_to='GST/') 
    Bpan_number = models.CharField(max_length=15)
    Bpan_image = models.FileField(upload_to='Bussiness pan card/')
    MSME_number = models.CharField(max_length=15)
    MSME_image = models.FileField(upload_to='MSME/')
    Contact_number = models.CharField(max_length=12)
    Bphoto_outer = models.FileField(upload_to='Bussiness photo/outer')
    Bphoto_inside = models.FileField(upload_to='Bussiness photo/inside')
    Busness_email = models.EmailField(max_length=50)
    VCname = models.CharField(max_length=50)
    VCmobile = models.CharField(max_length=12)
    VCaddress = models.CharField(max_length=150)
    
class Vendor_bank_details(models.Model) :
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE)
    bank_document = models.FileField(upload_to='Bank/')
    account_type = models.CharField(max_length=100)
    preffered_payout_date = models.CharField(max_length=10)
    account_holder_name = models.CharField(max_length=50)
    account_number = models.CharField(max_length=20)
    ifs_code = models.CharField(max_length=20)
    micr_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=20)
    
    
class Candidate(models.Model):
    refer_code = models.CharField(max_length=50)
    register_time = models.DateTimeField(default=now)
    employee_name = models.CharField(max_length=50, blank=True, null=True)
    candidate_name = models.CharField(max_length=255)
    unique_code = models.CharField(max_length=255)
    candidate_mobile_number = models.CharField(max_length=15)
    candidate_alternate_mobile_number = models.CharField(max_length=15, blank=True, null=True)
    candidate_email_address = models.EmailField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    lead_source = models.CharField(max_length=255,default='EVMS')
    preferred_location = models.CharField(max_length=255, blank=True, null=True)
    origin_location = models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255)
    diploma = models.CharField(max_length=255, blank=True, null=True)
    sector = models.CharField(max_length=255, blank=True, null=True)
    job_type = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    experience_year = models.CharField(max_length=255, blank=True, null=True)
    experience_month = models.CharField(max_length=255, blank=True, null=True)
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
    submit_by = models.CharField(max_length=100)
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
    
    def save(self, *args, **kwargs):
        if not self.unique_id:
            last_candidate = Candidate.objects.order_by('id').last()
            if last_candidate and last_candidate.unique_id:
                last_id_number = int(last_candidate.unique_id[4:])  # Extract the number part and convert to int
                new_id_number = last_id_number + 1
            else:
                new_id_number = 1
            self.unique_id = f"EVC{new_id_number:06d}"
        super().save(*args, **kwargs)
        