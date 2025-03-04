from django.shortcuts import render, redirect,get_object_or_404
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import datetime, time ,date
from django.utils.timezone import localtime
from django.db.models import Min, Max, Sum
import pytz
from datetime import datetime, time, timedelta
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import calendar
from calendar import monthrange
from django.db.models import Count, F
# from .utils import convert_number_to_words
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.utils import timezone,dateparse
from celery import shared_task
import re
from django.utils.timezone import localtime, make_aware
from datetime import datetime, timedelta, time
from EVMS.models import *
import openpyxl
from django.http import HttpResponse
from django.utils.timezone import localtime
from datetime import datetime
from django.db.models import Sum, Min, Max
from App.models import *

# Create your views here.

def custom_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("admin_candidate_list")  
        else:
            messages.error(request, "Invalid credentials or insufficient permissions.")
    return render(request, "hrms/admin-login.html")

def crm_dashboard(request):
    return render(request, "crm/crm-dashboard.html")

def admin_candidate_profile(request,id) :
    if request.user.is_staff or request.user.is_superuser:
        candidate = get_object_or_404(Candidate_registration, id=id)

        if request.method == 'POST':
            if 'candidate_personal_information' in request.POST:
                # Handle Employee fields
                candidate_name = request.POST.get('candidate_name')
                candidate_mobile_number = request.POST.get('candidate_mobile_number')
                candidate_email_address = request.POST.get('candidate_email_address')
                gender = request.POST.get('gender')
                lead_source = request.POST.get('lead_source')
                candidate_photo = request.FILES.get('candidate_photo')
                candidate_resume = request.FILES.get('candidate_resume')
                submit_by = request.POST.get('submit_by')
                
                candidate.candidate_name = candidate_name
                candidate.candidate_mobile_number = candidate_mobile_number
                candidate.candidate_email_address = candidate_email_address
                candidate.gender = gender
                candidate.lead_source = lead_source
                submit_by=submit_by
                if candidate_photo:
                    candidate.candidate_photo = candidate_photo
                if candidate_resume:
                    candidate.candidate_resume = candidate_resume
                candidate.save()

                messages.success(request, 'Candidate details updated successfully!')

            elif 'candidate_details' in request.POST:
                # Handle Emergency Contact fields
                candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
                preferred_location = request.POST.get('preferred_location')
                origin_location = request.POST.get('origin_location')
                qualification = request.POST.get('qualification')
                diploma = request.POST.get('diploma')
                sector = request.POST.get('sector')
                department = request.POST.get('department')
                experience_year = request.POST.get('experience_year')
                experience_month = request.POST.get('experience_month')
                current_company = request.POST.get('current_company')
                current_working_status = request.POST.get('current_working_status')
                current_salary = request.POST.get('current_salary')
                expected_salary = request.POST.get('expected_salary')
                submit_by = request.POST.get('submit_by')

                # Update EmergencyContact fields
                candidate.candidate_alternate_mobile_number = candidate_alternate_mobile_number
                candidate.preferred_location = preferred_location
                candidate.origin_location = origin_location
                candidate.qualification = qualification
                candidate.diploma = diploma
                candidate.sector = sector
                candidate.department = department
                candidate.experience_year = experience_year
                candidate.experience_month = experience_month
                candidate.current_company = current_company
                candidate.current_working_status = current_working_status
                candidate.current_salary = current_salary
                candidate.expected_salary = expected_salary
                submit_by=submit_by
                candidate.save()

                messages.success(request, 'Candidate details updated successfully!')
                
            elif 'submit_calling_remark' in request.POST:
                # Handle Social Media details form submission
                call_connection = request.POST.get('call_connection')
                calling_remark = request.POST.get('calling_remark')
                lead_generate = request.POST.get('lead_generate')
                send_for_interview = request.POST.get('send_for_interview')
                next_follow_up_date = request.POST.get('next_follow_up_date')
                submit_by = request.POST.get('submit_by')

                candidate.call_connection = call_connection
                candidate.calling_remark = calling_remark
                candidate.lead_generate = lead_generate
                candidate.send_for_interview = send_for_interview
                candidate.next_follow_up_date = next_follow_up_date
                candidate.submit_by = submit_by
                candidate.save()
                
                messages.success(request, 'Candidate Calling details updated successfully!')
                
            elif 'submit_secection_record' in request.POST:
                # Handle form submission for bank details
                selection_status = request.POST.get('selection_status')
                company_name = request.POST.get('company_name')
                offered_salary = request.POST.get('offered_salary')
                selection_date = request.POST.get('selection_date')
                candidate_joining_date = request.POST.get('candidate_joining_date')
                emta_commission = request.POST.get('emta_commission')
                payout_date = request.POST.get('payout_date')

                # Update or create bank details for the employee
                candidate.selection_status = selection_status
                candidate.company_name = company_name
                candidate.offered_salary = offered_salary
                candidate.selection_date = selection_date
                candidate.candidate_joining_date = candidate_joining_date
                candidate.emta_commission = emta_commission
                candidate.payout_date = payout_date
                candidate.save()

                messages.success(request, 'Secection details updated successfully!')
                
                

            return redirect('candidate-details', id=id)
        context = {
            'candidate': candidate
        }
        return render(request,'crm/candidate-profile.html',{'candidate':candidate})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
def admin_candidate_registration(request) :
    if request.user.is_staff or request.user.is_superuser:
        logged_in_employee = request.user
        if request.method == 'POST':
            candidate_name = request.POST.get('candidate_name')
            unique_code = request.POST.get('unique_code')
            candidate_mobile_number = request.POST.get('candidate_mobile_number')
            candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
            candidate_email_address = request.POST.get('candidate_email_address')
            gender = request.POST.get('gender')
            lead_source = request.POST.get('lead_source')
            preferred_location = request.POST.getlist('preferred_location')
            origin_location = request.POST.get('origin_location')
            qualification = request.POST.get('qualification')
            diploma = request.POST.get('diploma')
            sector = request.POST.getlist('sector')
            department = request.POST.getlist('department')
            experience_year = request.POST.get('experience_year')
            experience_month = request.POST.get('experience_month')
            current_company = request.POST.get('current_company')
            current_working_status = request.POST.get('current_working_status')
            current_salary = request.POST.get('current_salary')
            expected_salary = request.POST.get('expected_salary')
            candidate_photo = request.FILES.get('candidate_photo')
            candidate_resume = request.FILES.get('candidate_resume')
            call_connection = request.POST.get('call_connection')
            calling_remark = request.POST.get('calling_remark')
            lead_generate = request.POST.get('lead_generate')
            send_for_interview = request.POST.get('send_for_interview')
            next_follow_up_date = request.POST.get('next_follow_up_date')
            remark = request.POST.get('remark')
            submit_by = request.POST.get('submit_by')
            preferred_location_str = ', '.join(preferred_location)
            sector_str = ', '.join(sector)
            department_str = ', '.join(department)
            
            
            # Save to database
            Candidate_registration.objects.create(
                employee_name=logged_in_employee,
                candidate_name=candidate_name,
                unique_code=unique_code,
                candidate_mobile_number=candidate_mobile_number,
                candidate_alternate_mobile_number=candidate_alternate_mobile_number,
                candidate_email_address=candidate_email_address,
                gender = gender,
                lead_source=lead_source,
                preferred_location=preferred_location_str,
                origin_location=origin_location,
                qualification=qualification,
                diploma=diploma,
                sector = sector_str,
                department=department_str,
                experience_year=experience_year,
                experience_month=experience_month,
                current_company=current_company,
                current_working_status=current_working_status,
                current_salary = current_salary,
                expected_salary=expected_salary,
                call_connection=call_connection,
                calling_remark=calling_remark,
                lead_generate=lead_generate,
                send_for_interview=send_for_interview,
                next_follow_up_date = next_follow_up_date,
                candidate_photo=candidate_photo,
                candidate_resume=candidate_resume,
                remark=remark,
                submit_by=submit_by
                
            )
        
            return redirect('admin_candidate_list')
        
        suggested_unique_code = admin_get_next_unique_code()
        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha"
        ]
        job_sectors = [
        "IT (Information Technology)", "BPO (Business Process Outsourcing)","Banking and Finance",
        "Healthcare and Pharmaceuticals","Education and Training",
        "Retail and E-commerce", "Manufacturing and Production","Real Estate and Construction", "Hospitality and Tourism",
        "Media and Entertainment", "Telecommunications","Logistics and Supply Chain","Marketing and Advertising","Human Resources",
        "Legal and Compliance","Engineering and Infrastructure","Automobile Industry",
        "Fashion and Textile", "FMCG (Fast Moving Consumer Goods)",
        "Agriculture and Farming", "Insurance","Government Sector","NGO and Social Services",
        "Energy and Power","Aviation and Aerospace"
        ]
        departments = [
        # IT (Information Technology)
        "Software Development", "IT Support", "Web Development", 
        "Network Administration", "Cybersecurity", 
        "Data Science & Analytics", "Cloud Computing", "Quality Assurance (QA)",

        # BPO (Business Process Outsourcing)
        "Customer Support", "Technical Support", "Voice Process", 
        "Non-Voice Process", "Back Office Operations",

        # Banking and Finance
        "Investment Banking", "Retail Banking", "Loan Processing", 
        "Risk Management", "Accounting and Auditing", 
        "Financial Analysis", "Wealth Management",

        # Healthcare and Pharmaceuticals
        "Medical Representatives", "Clinical Research", "Nursing", 
        "Medical Technicians", "Pharmacy Operations", 
        "Healthcare Administration",

        # Education and Training
        "Teaching", "Curriculum Development", "Academic Counseling", 
        "E-Learning Development", "Education Administration",

        # Retail and E-commerce
        "Store Operations", "Supply Chain Management", 
        "Sales and Merchandising", "E-commerce Operations", "Digital Marketing",

        # Manufacturing and Production
        "Production Planning", "Quality Control", "Maintenance and Repair", 
        "Operations Management", "Inventory Management",

        # Real Estate and Construction
        "Sales and Marketing", "Civil Engineering", "Project Management", 
        "Interior Designing", "Surveying and Valuation",

        # Hospitality and Tourism
        "Hotel Management", "Travel Coordination", "Event Planning", 
        "Food and Beverage Services", "Guest Relations",

        # Media and Entertainment
        "Content Writing", "Video Editing", "Graphic Designing", 
        "Social Media Management", "Event Production",

        # Telecommunications
        "Network Installation", "Customer Support", "Telecom Engineering", 
        "Technical Operations", "Business Development",

        # Logistics and Supply Chain
        "Logistics Coordination", "Warehouse Management", "Procurement", 
        "Transportation Management", "Inventory Control",

        # Marketing and Advertising
        "Market Research", "Brand Management", "Advertising Sales", 
        "Public Relations", "Digital Marketing",

        # Human Resources
        "Recruitment", "Employee Relations", "Payroll and Benefits", 
        "Training and Development", "HR Analytics",

        # Legal and Compliance
        "Corporate Law", "Compliance Auditing", "Contract Management", 
        "Intellectual Property Rights", "Legal Advisory",

        # Engineering and Infrastructure
        "Civil Engineering", "Mechanical Engineering", 
        "Electrical Engineering", "Project Planning", "Structural Design",

        # Automobile Industry
        "Automotive Design", "Production and Assembly", "Sales and Service", 
        "Supply Chain Management", "Quality Assurance",

        # Fashion and Textile
        "Fashion Design", "Merchandising", "Production Management", 
        "Quality Control", "Retail Sales",

        # FMCG (Fast Moving Consumer Goods)
        "Sales and Marketing", "Supply Chain Operations", 
        "Production Management", "Quality Control", "Brand Management",

        # Agriculture and Farming
        "Agribusiness Management", "Farm Operations", "Food Processing", 
        "Agricultural Sales", "Quality Assurance",

        # Insurance
        "Sales and Business Development", "Underwriting", 
        "Claims Management", "Actuarial Services", "Policy Administration",

        # Government Sector
        "Administrative Services", "Public Relations", 
        "Policy Analysis", "Clerical Positions", "Field Operations",

        # NGO and Social Services
        "Community Development", "Fundraising", "Program Management", 
        "Volunteer Coordination", "Policy Advocacy",

        # Energy and Power
        "Renewable Energy Operations", "Power Plant Engineering", 
        "Energy Efficiency Management", "Electrical Design", "Maintenance",

        # Aviation and Aerospace
        "Flight Operations", "Ground Staff", "Aircraft Maintenance", 
        "Cabin Crew", "Research and Development"
        ]


        context = {
            'suggested_unique_code':suggested_unique_code,
            'districts' : districts,
            'job_sectors' : job_sectors,
            'departments' : departments
        }
        return render (request,'crm/candidate-registration.html',context)    
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
def admin_get_next_unique_code():
    candidate = Candidate_registration.objects.filter(unique_code__regex=r'^EC\d{6}$').values_list('unique_code', flat=True)
    numbers = [int(re.search(r'\d{6}', unique_code).group()) for unique_code in candidate]

    if numbers:
        next_number = max(numbers) + 1  
    else:
        next_number = 1 
    return f"EC{next_number:06d}"

def admin_candidate_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        candidates = Candidate_registration.objects.all().order_by('-id')
        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha"
        ]
        return render (request,'crm/candidate-list.html',{'candidates':candidates,'districts':districts})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
    
def admin_company_list(request) :
    companys = Company_registration.objects.all().order_by('-id')
    return render(request,'crm/company-list.html',{'companys':companys})

def admin_company_profile(request,id) :
    company = get_object_or_404(Company_registration, id=id)
    if request.method == 'POST':
        if 'company_personal_information' in request.POST:
            # Handle Employee fields
            company_name = request.POST.get('company_name')
            vacancy_status = request.POST.get('vacancy_status')
            company_location = request.POST.get('company_location')
            company_unique_code = request.POST.get('company_unique_code')
            job_profile = request.POST.get('job_profile')
            company_vacancy_unique_code = request.POST.get('company_vacancy_unique_code')
            company_logo = request.FILES.get('company_logo')
            vacancy_opening_date = request.POST.get('vacancy_opening_date')
            company_email_address = request.POST.get('company_email_address')
            
            company.company_name = company_name
            company.company_location = company_location
            company.company_unique_code = company_unique_code
            company.job_profile = job_profile
            company.company_vacancy_unique_code = company_vacancy_unique_code
            company.company_email_address=company_email_address
            company.vacancy_status=vacancy_status
            if company_logo:
                company.company_logo = company_logo
            company.vacancy_opening_date = vacancy_opening_date
            company.save()

            messages.success(request, 'Company details updated successfully!')

        elif 'company_details' in request.POST:
            # Handle Emergency Contact fields
            company_contact_person_name = request.POST.get('company_contact_person_name')
            company_contact_person_contact_details = request.POST.get('company_contact_person_contact_details')
            company_contact_person_designation = request.POST.get('company_contact_person_designation')
            interview_address = request.POST.get('interview_address')
            payroll = request.POST.get('payroll')
            minimum_salary_range = request.POST.get('minimum_salary_range')
            maximum_salary_range = request.POST.get('maximum_salary_range')
            job_opening_origin = request.POST.get('job_opening_origin')
            sector_type = request.POST.get('sector_type')
            department_name = request.POST.get('department_name')
            fresher_status = request.POST.get('fresher_status')
            minimum_age = request.POST.get('minimum_age')
            maximum_age = request.POST.get('maximum_age')
            gender = request.POST.get('gender')
             # Handle form submission for bank details
            minimum_experience = request.POST.get('minimum_experience')
            maximum_experience = request.POST.get('maximum_experience')
            minimum_education_qualification = request.POST.get('minimum_education_qualification')
            specialization = request.POST.get('specialization')
            vacancy_closing_date = request.POST.get('vacancy_closing_date')
            
            # Update EmergencyContact fields
            company.company_contact_person_name = company_contact_person_name
            company.company_contact_person_contact_details = company_contact_person_contact_details
            company.company_contact_person_designation = company_contact_person_designation
            company.interview_address = interview_address
            company.payroll = payroll
            company.minimum_salary_range = minimum_salary_range
            company.maximum_salary_range = maximum_salary_range
            company.job_opening_origin = job_opening_origin
            company.sector_type = sector_type
            company.department_name = department_name
            company.fresher_status = fresher_status
            company.minimum_age = minimum_age
            company.maximum_age = maximum_age
            company.gender=gender
            company.minimum_experience = minimum_experience
            company.maximum_experience = maximum_experience
            company.minimum_education_qualification = minimum_education_qualification
            company.specialization = specialization
            company.vacancy_closing_date = vacancy_closing_date
            company.save()

            messages.success(request, 'company details updated successfully!')
            
        elif 'submit_calling_remark' in request.POST:
            # Handle Social Media details form submission
            company_usp = request.POST.get('company_usp')
            status_of_incentive = request.POST.get('status_of_incentive')
            status_of_proposal = request.POST.get('status_of_proposal')
            invoice_generation_date = request.POST.get('invoice_generation_date')
            payout_date = request.POST.get('payout_date')
            payment_condiation = request.POST.get('payment_condiation')
            replacement_criteria = request.POST.get('replacement_criteria')
            remark = request.POST.get('remark')
            specialization = request.POST.get('specialization')
            vacancy_closing_date = request.POST.get('vacancy_closing_date')

            company.company_usp = company_usp
            company.status_of_incentive = status_of_incentive
            company.status_of_proposal = status_of_proposal
            company.invoice_generation_date = invoice_generation_date
            company.payout_date = payout_date
            company.payment_condiation = payment_condiation
            company.replacement_criteria = replacement_criteria
            company.remark = remark
            company.specialization = specialization
            company.vacancy_closing_date = vacancy_closing_date
            company.save()
            
            messages.success(request, 'company Calling details updated successfully!')
        return redirect('admin_company_profile', id=id)
    return render(request,'crm/company-profile.html',{'company':company})


def admin_vendor_list(request) :
    vendors = Vendor.objects.all().order_by('-id')
    return render(request,'crm/admin-vendor-list.html',{'vendors':vendors})

def admin_evms_candidate_list(request) :
    candidates = Candidate.objects.all().order_by('-id')
    return render(request,'crm/admin-evms-candidate-list.html',{'candidates':candidates})

# def admin_vendor_candidate_list(request,id) :
#     vendor = get_object_or_404(Vendor, id=id)
    
#     return render(request,'crm/admin-vendor-candidate-list.html',{'candidates':candidates,'vendor':vendor})

def admin_vendor_candidate_list(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    candidates = Candidate.objects.filter(refer_code=vendor.refer_code).order_by('-id')
    vendor_profile_detail, _ = Vendor_profile_details.objects.get_or_create(vendor=vendor)
    vendor_bussiness_detail, _ = Vendor_bussiness_details.objects.get_or_create(vendor=vendor)
    vendor_bank_detail, _ = Vendor_bank_details.objects.get_or_create(vendor=vendor)

    if request.method == 'POST':
        if 'submit_vendor_profile_details' in request.POST:
            # Handle Employee fields
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            mobile_number = request.POST.get('mobile_number')
            email = request.POST.get('email')
            vendor_profile_image = request.FILES.get('vendor_profile_image')
            date_of_birth = request.POST.get('date_of_birth')
            
            vendor.first_name = first_name
            vendor.last_name = last_name
            vendor.mobile_number = mobile_number
            vendor.email = email
            vendor.date_of_birth = date_of_birth
            
            if vendor_profile_image:
                vendor.vendor_profile_image = vendor_profile_image
            vendor.save()
            gender = request.POST.get('gender')
            address = request.POST.get('address')
            adhar_card_number = request.POST.get('adhar_card_number')
            adhar_card_image = request.FILES.get('adhar_card_image')
            pan_card_number = request.POST.get('pan_card_number')
            pan_card_image = request.FILES.get('pan_card_image')
            location = request.POST.get('location')
            vendor_profile_detail.gender = gender
            vendor_profile_detail.address = address
            vendor_profile_detail.adhar_card_number = adhar_card_number
            vendor_profile_detail.pan_card_number = pan_card_number
            vendor_profile_detail.location = location
            if adhar_card_image:
                vendor_profile_detail.adhar_card_image = adhar_card_image
            if pan_card_image:
                vendor_profile_detail.pan_card_image = pan_card_image    
            vendor_profile_detail.save()

            messages.success(request, 'Profile details updated successfully!')

        elif 'submit_vendor_bussiness_details' in request.POST:
            # Handle Emergency Contact fields
            shop_name = request.POST.get('shop_name')
            Contact_number = request.POST.get('Contact_number')
            Busness_email = request.POST.get('Busness_email')
            Gumasta_number = request.POST.get('Gumasta_number')
            gumasta_image = request.FILES.get('gumasta_image')
            gst_number = request.POST.get('gst_number')
            gst_image = request.FILES.get('gst_image')

            Bpan_number = request.POST.get('Bpan_number')
            Bpan_image = request.FILES.get('Bpan_image')
            MSME_number = request.POST.get('MSME_number')
            MSME_image = request.FILES.get('MSME_image')
            Bphoto_outer = request.FILES.get('Bphoto_outer')
            
            Bphoto_inside = request.FILES.get('Bphoto_inside')
            VCname = request.POST.get('VCname')
            VCmobile = request.POST.get('VCmobile')
            VCaddress = request.POST.get('VCaddress')

            # Update EmergencyContact fields
            vendor_bussiness_detail.shop_name = shop_name
            vendor_bussiness_detail.Contact_number = Contact_number
            vendor_bussiness_detail.Busness_email = Busness_email
            vendor_bussiness_detail.Gumasta_number = Gumasta_number
            vendor_bussiness_detail.gst_number = gst_number
            vendor_bussiness_detail.Bpan_number = Bpan_number
            vendor_bussiness_detail.MSME_number = MSME_number
            vendor_bussiness_detail.VCname = VCname
            vendor_bussiness_detail.VCmobile = VCmobile
            vendor_bussiness_detail.VCaddress = VCaddress
            
            if gst_image:
                vendor_bussiness_detail.gst_image = gst_image
            if gumasta_image:
                vendor_bussiness_detail.gumasta_image = gumasta_image    
            if Bpan_image:
                vendor_bussiness_detail.Bpan_image = Bpan_image
            if MSME_image:
                vendor_bussiness_detail.MSME_image = MSME_image    
            if Bphoto_outer:
                vendor_bussiness_detail.Bphoto_outer = Bphoto_outer
            if Bphoto_inside:
                vendor_bussiness_detail.Bphoto_inside = Bphoto_inside    
            vendor_bussiness_detail.save()

            messages.success(request, 'Bussiness details updated successfully!')
            
        elif 'submit_vendor_bank_details' in request.POST:
            # Handle form submission for bank details
            account_holder_name = request.POST.get('account_holder_name')
            bank_name = request.POST.get('bank_name')
            account_number = request.POST.get('account_number')
            confirm_account_number = request.POST.get('confirm_account_number')
            ifs_code = request.POST.get('ifs_code')
            account_type = request.POST.get('account_type')
            micr_code = request.POST.get('micr_code')
            bank_document = request.FILES.get('bank_document')
            preffered_payout_date = request.POST.get('preffered_payout_date')

            # Ensure account number and confirm account number match
            if account_number != confirm_account_number:
                messages.error(request, "Account numbers do not match!")
                return redirect('employee-bank-details', id=employee.id)  # Redirect back to the same page

            # Update or create bank details for the employee
            vendor_bank_detail.account_holder_name = account_holder_name
            vendor_bank_detail.bank_name = bank_name
            vendor_bank_detail.account_number = account_number
            vendor_bank_detail.confirm_account_number = confirm_account_number
            vendor_bank_detail.ifs_code = ifs_code
            vendor_bank_detail.micr_code = micr_code
            vendor_bank_detail.account_type = account_type
            vendor_bank_detail.preffered_payout_date = preffered_payout_date
            if bank_document:
                vendor_bank_detail.bank_document = bank_document  
            vendor_bank_detail.save()

            messages.success(request, 'Bank details updated successfully!')
            
            

        return redirect('admin_vendor_candidate_list', id=vendor.id)  # Adjust 'employee-details' to your URL name
    districts = [
        "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
        "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
        "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
        "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
        "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
        "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
        "Ujjain", "Umaria", "Vidisha"
    ]
    context = {
        'vendor': vendor,
        'vendor_profile_detail': vendor_profile_detail,
        'vendor_bussiness_detail': vendor_bussiness_detail,
        'vendor_bank_detail': vendor_bank_detail,
        'districts' : districts,
        'candidates' : candidates
    }
    return render(request, 'crm/admin-vendor-candidate-list.html', context)




def evms_candidate_profile(request,id) :
    candidate = get_object_or_404(Candidate, id=id)
    employees = Employee.objects.all()
    if request.method == 'POST':
        if 'candidate_personal_information' in request.POST:
            # Handle Employee fields
            candidate_name = request.POST.get('candidate_name')
            employee_name = request.POST.get('employee_name')
            candidate_mobile_number = request.POST.get('candidate_mobile_number')
            candidate_email_address = request.POST.get('candidate_email_address')
            gender = request.POST.get('gender')
            lead_source = request.POST.get('lead_source')
            candidate_photo = request.FILES.get('candidate_photo')
            candidate_resume = request.FILES.get('candidate_resume')
            submit_by = request.POST.get('submit_by')
            
            candidate.candidate_name = candidate_name
            candidate.employee_name = employee_name
            candidate.candidate_mobile_number = candidate_mobile_number
            candidate.candidate_email_address = candidate_email_address
            candidate.gender = gender
            candidate.lead_source = lead_source
            submit_by=submit_by
            if candidate_photo:
                candidate.candidate_photo = candidate_photo
            if candidate_resume:
                candidate.candidate_resume = candidate_resume
            candidate.save()

            messages.success(request, 'Candidate details updated successfully!')

        elif 'candidate_details' in request.POST:
            # Handle Emergency Contact fields
            candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
            preferred_location = request.POST.get('preferred_location')
            origin_location = request.POST.get('origin_location')
            qualification = request.POST.get('qualification')
            diploma = request.POST.get('diploma')
            sector = request.POST.get('sector')
            department = request.POST.get('department')
            experience_year = request.POST.get('experience_year')
            experience_month = request.POST.get('experience_month')
            current_company = request.POST.get('current_company')
            current_working_status = request.POST.get('current_working_status')
            current_salary = request.POST.get('current_salary')
            expected_salary = request.POST.get('expected_salary')
            submit_by = request.POST.get('submit_by')

            # Update EmergencyContact fields
            candidate.candidate_alternate_mobile_number = candidate_alternate_mobile_number
            candidate.preferred_location = preferred_location
            candidate.origin_location = origin_location
            candidate.qualification = qualification
            candidate.diploma = diploma
            candidate.sector = sector
            candidate.department = department
            candidate.experience_year = experience_year
            candidate.experience_month = experience_month
            candidate.current_company = current_company
            candidate.current_working_status = current_working_status
            candidate.current_salary = current_salary
            candidate.expected_salary = expected_salary
            submit_by=submit_by
            candidate.save()

            messages.success(request, 'Candidate details updated successfully!')
            
        elif 'submit_calling_remark' in request.POST:
            # Handle Social Media details form submission
            call_connection = request.POST.get('call_connection')
            calling_remark = request.POST.get('calling_remark')
            lead_generate = request.POST.get('lead_generate')
            send_for_interview = request.POST.get('send_for_interview')
            next_follow_up_date = request.POST.get('next_follow_up_date')
            submit_by = request.POST.get('submit_by')

            candidate.call_connection = call_connection
            candidate.calling_remark = calling_remark
            candidate.lead_generate = lead_generate
            candidate.send_for_interview = send_for_interview
            candidate.next_follow_up_date = next_follow_up_date
            candidate.submit_by = submit_by
            candidate.save()
            
            messages.success(request, 'Candidate Calling details updated successfully!')
            
        elif 'submit_secection_record' in request.POST:
            # Handle form submission for bank details
            selection_status = request.POST.get('selection_status')
            company_name = request.POST.get('company_name')
            offered_salary = request.POST.get('offered_salary')
            selection_date = request.POST.get('selection_date')
            candidate_joining_date = request.POST.get('candidate_joining_date')
            emta_commission = request.POST.get('emta_commission')
            payout_date = request.POST.get('payout_date')

            # Update or create bank details for the employee
            candidate.selection_status = selection_status
            candidate.company_name = company_name
            candidate.offered_salary = offered_salary
            candidate.selection_date = selection_date
            candidate.candidate_joining_date = candidate_joining_date
            candidate.emta_commission = emta_commission
            candidate.payout_date = payout_date
            candidate.save()

            messages.success(request, 'Secection details updated successfully!')
            
            

        return redirect('evms_candidate_profile', id=id)
    context = {
        'candidate': candidate,
        'employees' : employees
    }
    return render(request,'crm/evms-candidate-profile.html ',context)

def evms_vendor_candidate_profile(request,id) :
    candidate = get_object_or_404(Candidate, id=id)
    employees = Employee.objects.all()
    if request.method == 'POST':
        if 'candidate_personal_information' in request.POST:
            # Handle Employee fields
            candidate_name = request.POST.get('candidate_name')
            employee_name = request.POST.get('employee_name')
            candidate_mobile_number = request.POST.get('candidate_mobile_number')
            candidate_email_address = request.POST.get('candidate_email_address')
            gender = request.POST.get('gender')
            lead_source = request.POST.get('lead_source')
            candidate_photo = request.FILES.get('candidate_photo')
            candidate_resume = request.FILES.get('candidate_resume')
            submit_by = request.POST.get('submit_by')
            
            candidate.candidate_name = candidate_name
            candidate.employee_name = employee_name
            candidate.candidate_mobile_number = candidate_mobile_number
            candidate.candidate_email_address = candidate_email_address
            candidate.gender = gender
            candidate.lead_source = lead_source
            submit_by=submit_by
            if candidate_photo:
                candidate.candidate_photo = candidate_photo
            if candidate_resume:
                candidate.candidate_resume = candidate_resume
            candidate.save()

            messages.success(request, 'Candidate details updated successfully!')

        elif 'candidate_details' in request.POST:
            # Handle Emergency Contact fields
            candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
            preferred_location = request.POST.get('preferred_location')
            origin_location = request.POST.get('origin_location')
            qualification = request.POST.get('qualification')
            diploma = request.POST.get('diploma')
            sector = request.POST.get('sector')
            department = request.POST.get('department')
            experience_year = request.POST.get('experience_year')
            experience_month = request.POST.get('experience_month')
            current_company = request.POST.get('current_company')
            current_working_status = request.POST.get('current_working_status')
            current_salary = request.POST.get('current_salary')
            expected_salary = request.POST.get('expected_salary')
            submit_by = request.POST.get('submit_by')

            # Update EmergencyContact fields
            candidate.candidate_alternate_mobile_number = candidate_alternate_mobile_number
            candidate.preferred_location = preferred_location
            candidate.origin_location = origin_location
            candidate.qualification = qualification
            candidate.diploma = diploma
            candidate.sector = sector
            candidate.department = department
            candidate.experience_year = experience_year
            candidate.experience_month = experience_month
            candidate.current_company = current_company
            candidate.current_working_status = current_working_status
            candidate.current_salary = current_salary
            candidate.expected_salary = expected_salary
            submit_by=submit_by
            candidate.save()

            messages.success(request, 'Candidate details updated successfully!')
            
        elif 'submit_calling_remark' in request.POST:
            # Handle Social Media details form submission
            call_connection = request.POST.get('call_connection')
            calling_remark = request.POST.get('calling_remark')
            lead_generate = request.POST.get('lead_generate')
            send_for_interview = request.POST.get('send_for_interview')
            next_follow_up_date = request.POST.get('next_follow_up_date')
            submit_by = request.POST.get('submit_by')

            candidate.call_connection = call_connection
            candidate.calling_remark = calling_remark
            candidate.lead_generate = lead_generate
            candidate.send_for_interview = send_for_interview
            candidate.next_follow_up_date = next_follow_up_date
            candidate.submit_by = submit_by
            candidate.save()
            
            messages.success(request, 'Candidate Calling details updated successfully!')
            
        elif 'submit_secection_record' in request.POST:
            # Handle form submission for bank details
            selection_status = request.POST.get('selection_status')
            company_name = request.POST.get('company_name')
            offered_salary = request.POST.get('offered_salary')
            selection_date = request.POST.get('selection_date')
            candidate_joining_date = request.POST.get('candidate_joining_date')
            emta_commission = request.POST.get('emta_commission')
            payout_date = request.POST.get('payout_date')

            # Update or create bank details for the employee
            candidate.selection_status = selection_status
            candidate.company_name = company_name
            candidate.offered_salary = offered_salary
            candidate.selection_date = selection_date
            candidate.candidate_joining_date = candidate_joining_date
            candidate.emta_commission = emta_commission
            candidate.payout_date = payout_date
            candidate.save()

            messages.success(request, 'Secection details updated successfully!')
            
            

        return redirect('evms_vendor_candidate_profile', id=id)
    context = {
        'candidate': candidate,
        'employees' : employees
    }
    return render(request,'crm/evms-vendor-candidate-profile.html',context)

def download_attendance_excel(request, user_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Unauthorized", status=403)

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        return HttpResponse("Invalid Date Range", status=400)

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponse("Invalid Date Format", status=400)

    # Fetch holidays and leaves
    holidays = set(Holiday.objects.filter(date__range=(start_date, end_date)).values_list('date', flat=True))
    leave_days = set(LeaveRequest.objects.filter(
        employee__user_id=user_id,
        start_date__lte=end_date, end_date__gte=start_date,
        status="Approved"
    ).values_list('start_date', flat=True))

    # Fetch attendance data
    attendance_data = (
        EmployeeSession.objects.filter(
            user_id=user_id, login_time__date__range=(start_date, end_date)
        )
        .values("login_time__date")
        .annotate(
            first_login=Min("login_time"),
            last_logout=Max("logout_time"),
            total_time=Sum("total_time"),
            login_count=Count("id"),
            logout_reason=Max("logout_reason")
        )
        .order_by("login_time__date")
    )

    # Create an Excel workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Data"

    # Header row
    headers = ["Date", "Status", "First Login", "Last Logout", "Logout Reason", "Total Time", "Login Count"]
    ws.append(headers)

    # Generate attendance data for each day
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    attendance_dict = {record["login_time__date"]: record for record in attendance_data}

    for day in date_range:
        status = "Absent"
        record = attendance_dict.get(day, None)

        if day in holidays:
            status = "Holiday"
        elif day in leave_days:
            status = "On Leave"
        elif record:
            if record["total_time"] and record["total_time"].total_seconds() > 14400:  # More than 4 hours
                status = "Present"
            elif record["total_time"] and 0 < record["total_time"].total_seconds() <= 14400:
                status = "Half-Day"

        ws.append([
            day.strftime("%Y-%m-%d"),
            status,
            localtime(record["first_login"]).strftime("%Y-%m-%d %H:%M:%S") if record and record["first_login"] else "N/A",
            localtime(record["last_logout"]).strftime("%Y-%m-%d %H:%M:%S") if record and record["last_logout"] else "N/A",
            record["logout_reason"] if record and record["logout_reason"] else "Currently Working",
            str(record["total_time"]) if record and record["total_time"] else "N/A",
            record["login_count"] if record else 0,
        ])

    # Generate response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="Attendance_{user_id}.xlsx"'
    wb.save(response)

    return response

def admin_company_registration(request):
    if request.method == 'POST':
        # Capture form data from POST request
        employee_name = request.POST.get('employee_name')
        company_name = request.POST.get('company_name')
        company_logo = request.FILES.get('company_logo')
        company_location = request.POST.getlist('company_location')
        company_unique_code = request.POST.get('company_unique_code')
        job_profile = request.POST.get('job_profile')
        company_vacancy_unique_code = request.POST.get('company_vacancy_unique_code')
        vacancy_opening_date = request.POST.get('vacancy_opening_date')
        company_email_address = request.POST.get('company_email_address')
        vacancy_status = request.POST.get('vacancy_status','Pending')
        company_contact_person_name = request.POST.get('company_contact_person_name')
        company_contact_person_contact_details = request.POST.get('company_contact_person_contact_details')
        company_contact_person_designation = request.POST.get('company_contact_person_designation')
        interview_address = request.POST.get('interview_address')
        payroll = request.POST.get('payroll')
        third_party_name = request.POST.get('third_party_name')
        job_opening_origin = request.POST.get('job_opening_origin')
        sector_type = request.POST.getlist('sector_type')
        department_name = request.POST.getlist('department_name')
        fresher_status = request.POST.get('fresher_status')
        minimum_age = request.POST.get('minimum_age')
        maximum_age = request.POST.get('maximum_age')
        gender = request.POST.get('gender')
        minimum_experience = request.POST.get('minimum_experience')
        maximum_experience = request.POST.get('maximum_experience')
        minimum_education_qualification = request.POST.get('minimum_education_qualification')
        specialization = request.POST.get('specialization')
        minimum_salary_range = request.POST.get('minimum_salary_range')
        maximum_salary_range = request.POST.get('maximum_salary_range')
        vacancy_closing_date = request.POST.get('vacancy_closing_date')
        special_instruction = request.POST.get('special_instruction')
        company_usp = request.POST.get('company_usp')
        status_of_incentive = request.POST.get('status_of_incentive')
        status_of_proposal = request.POST.get('status_of_proposal')
        invoice_generation_date = request.POST.get('invoice_generation_date')
        payout_date = request.POST.get('payout_date')
        payment_condiation = request.POST.get('payment_condiation')
        replacement_criteria = request.POST.get('replacement_criteria')
        remark = request.POST.get('remark')
        company_location_str = ', '.join(company_location)

        # Create a new Company_registration record
        Company_registration.objects.create(
            employee_name=employee_name,
            company_name=company_name,
            company_logo = company_logo,
            company_location=company_location_str,
            company_unique_code=company_unique_code,
            company_vacancy_unique_code=company_vacancy_unique_code,
            vacancy_opening_date=vacancy_opening_date,
            company_email_address=company_email_address,
            vacancy_status=vacancy_status,
            company_contact_person_name=company_contact_person_name,
            company_contact_person_contact_details=company_contact_person_contact_details,
            company_contact_person_designation=company_contact_person_designation,
            interview_address=interview_address,
            payroll=payroll,
            third_party_name=third_party_name,
            job_opening_origin=job_opening_origin,
            sector_type=sector_type,
            department_name=department_name,
            job_profile=job_profile,
            fresher_status=fresher_status,
            minimum_age=minimum_age,
            maximum_age=maximum_age,
            gender=gender,
            minimum_experience=minimum_experience,
            maximum_experience=maximum_experience,
            minimum_education_qualification=minimum_education_qualification,
            specialization=specialization,
            minimum_salary_range=minimum_salary_range,
            maximum_salary_range=maximum_salary_range,
            vacancy_closing_date=vacancy_closing_date,
            special_instruction=special_instruction,
            company_usp=company_usp,
            status_of_incentive=status_of_incentive,
            status_of_proposal=status_of_proposal,
            invoice_generation_date=invoice_generation_date,
            payout_date=payout_date,
            payment_condiation=payment_condiation,
            replacement_criteria=replacement_criteria,
            remark=remark,
        )

        # Redirect to the same page after saving
        return redirect('admin_company_list')
    districts = [
        "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
        "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
        "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
        "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
        "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
        "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
        "Ujjain", "Umaria", "Vidisha"
    ]
    job_sectors = [
    "IT (Information Technology)", "BPO (Business Process Outsourcing)","Banking and Finance",
    "Healthcare and Pharmaceuticals","Education and Training",
    "Retail and E-commerce", "Manufacturing and Production","Real Estate and Construction", "Hospitality and Tourism",
    "Media and Entertainment", "Telecommunications","Logistics and Supply Chain","Marketing and Advertising","Human Resources",
    "Legal and Compliance","Engineering and Infrastructure","Automobile Industry",
    "Fashion and Textile", "FMCG (Fast Moving Consumer Goods)",
    "Agriculture and Farming", "Insurance","Government Sector","NGO and Social Services",
    "Energy and Power","Aviation and Aerospace"
    ]
    departments = [
    # IT (Information Technology)
    "Software Development", "IT Support", "Web Development", 
    "Network Administration", "Cybersecurity", 
    "Data Science & Analytics", "Cloud Computing", "Quality Assurance (QA)",

    # BPO (Business Process Outsourcing)
    "Customer Support", "Technical Support", "Voice Process", 
    "Non-Voice Process", "Back Office Operations",

    # Banking and Finance
    "Investment Banking", "Retail Banking", "Loan Processing", 
    "Risk Management", "Accounting and Auditing", 
    "Financial Analysis", "Wealth Management",

    # Healthcare and Pharmaceuticals
    "Medical Representatives", "Clinical Research", "Nursing", 
    "Medical Technicians", "Pharmacy Operations", 
    "Healthcare Administration",

    # Education and Training
    "Teaching", "Curriculum Development", "Academic Counseling", 
    "E-Learning Development", "Education Administration",

    # Retail and E-commerce
    "Store Operations", "Supply Chain Management", 
    "Sales and Merchandising", "E-commerce Operations", "Digital Marketing",

    # Manufacturing and Production
    "Production Planning", "Quality Control", "Maintenance and Repair", 
    "Operations Management", "Inventory Management",

    # Real Estate and Construction
    "Sales and Marketing", "Civil Engineering", "Project Management", 
    "Interior Designing", "Surveying and Valuation",

    # Hospitality and Tourism
    "Hotel Management", "Travel Coordination", "Event Planning", 
    "Food and Beverage Services", "Guest Relations",

    # Media and Entertainment
    "Content Writing", "Video Editing", "Graphic Designing", 
    "Social Media Management", "Event Production",

    # Telecommunications
    "Network Installation", "Customer Support", "Telecom Engineering", 
    "Technical Operations", "Business Development",

    # Logistics and Supply Chain
    "Logistics Coordination", "Warehouse Management", "Procurement", 
    "Transportation Management", "Inventory Control",

    # Marketing and Advertising
    "Market Research", "Brand Management", "Advertising Sales", 
    "Public Relations", "Digital Marketing",

    # Human Resources
    "Recruitment", "Employee Relations", "Payroll and Benefits", 
    "Training and Development", "HR Analytics",

    # Legal and Compliance
    "Corporate Law", "Compliance Auditing", "Contract Management", 
    "Intellectual Property Rights", "Legal Advisory",

    # Engineering and Infrastructure
    "Civil Engineering", "Mechanical Engineering", 
    "Electrical Engineering", "Project Planning", "Structural Design",

    # Automobile Industry
    "Automotive Design", "Production and Assembly", "Sales and Service", 
    "Supply Chain Management", "Quality Assurance",

    # Fashion and Textile
    "Fashion Design", "Merchandising", "Production Management", 
    "Quality Control", "Retail Sales",

    # FMCG (Fast Moving Consumer Goods)
    "Sales and Marketing", "Supply Chain Operations", 
    "Production Management", "Quality Control", "Brand Management",

    # Agriculture and Farming
    "Agribusiness Management", "Farm Operations", "Food Processing", 
    "Agricultural Sales", "Quality Assurance",

    # Insurance
    "Sales and Business Development", "Underwriting", 
    "Claims Management", "Actuarial Services", "Policy Administration",

    # Government Sector
    "Administrative Services", "Public Relations", 
    "Policy Analysis", "Clerical Positions", "Field Operations",

    # NGO and Social Services
    "Community Development", "Fundraising", "Program Management", 
    "Volunteer Coordination", "Policy Advocacy",

    # Energy and Power
    "Renewable Energy Operations", "Power Plant Engineering", 
    "Energy Efficiency Management", "Electrical Design", "Maintenance",

    # Aviation and Aerospace
    "Flight Operations", "Ground Staff", "Aircraft Maintenance", 
    "Cabin Crew", "Research and Development"
    ]
    

    # Render the template with the context
    return render(request, 'crm/company-registration.html',{
        'districts' : districts,
        'job_sectors' : job_sectors,
        'departments' : departments
        })
