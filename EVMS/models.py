from django.db import models
from django.contrib.auth.models import User

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
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    qualification = models.CharField(max_length = 100)
    mobile_number = models.BigIntegerField()
    email = models.EmailField()
    status = models.CharField(max_length=10, default='Pending')
    Contact = models.CharField(max_length=10 , default='No')
    resume = models.FileField(upload_to='candidate/resume/')
    sector = models.CharField(max_length=50)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    location = models.CharField(max_length=50)
    totalCommission = models.CharField(max_length=100, default='0')
    Contact_by = models.CharField(max_length=50,default='None')
    Remark = models.CharField(max_length=200)
    commission_Generate_date = models.CharField(max_length=20,default=0)
    Payment_Status = models.CharField(max_length=30, default='Pending')
    Job_Type = models.CharField(max_length=30)
    Payment_complete_date = models.CharField(max_length=20)
    authentication_status = models.CharField(max_length=20)
    submission_time = models.DateTimeField()
    candidate_image = models.ImageField(upload_to='candidate_images/', null=True, blank=True)
    unique_id = models.CharField(max_length=10, unique=True, blank=True, null=True)

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
        