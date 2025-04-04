from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404, render, redirect
from .urls import *
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum,Max,Count
import random
import requests
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse
import io
import pandas as pd
import pytz
from django.http import JsonResponse
import re
import os


def vendor_signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile_number = request.POST.get('mobile_number')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        refer_code = username

        if not username:
            messages.error(request, 'Username must be set')
            return render(request, 'vendor-signup.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'evms/vendor-signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken')
            return render(request, 'evms/vendor-signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already taken')
            return render(request, 'evms/vendor-signup.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        vendor = Vendor.objects.create(user=user, mobile_number=mobile_number, refer_code=refer_code)

        return redirect('vendor_login')

    # Suggest next username in the format EMTA0001
    suggested_username = get_next_username()

    return render(request, 'evms/vendor-signup.html', {'suggested_username': suggested_username})

def get_next_username():
    # Get all usernames that start with 'EMTA' and end with 4 digits
    users = User.objects.filter(username__regex=r'^EMTA\d{4}$').values_list('username', flat=True)

    # Extract the numeric part from each username
    numbers = [int(re.search(r'\d{4}', username).group()) for username in users]

    if numbers:
        next_number = max(numbers) + 1  # Increment the max number found
    else:
        next_number = 1  # Start with EMTA0001 if no usernames exist

    # Format the next username with leading zeros (e.g., EMTA0001)
    return f"EMTA{next_number:04d}"

def vendor_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        remember_me = request.POST.get('remember_me')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if remember_me:
                request.session.set_expiry(settings.REMEMBER_ME_EXPIRY)
                request.session['remember_me'] = True
            else:
                request.session.pop('remember_me', None)
            return redirect('vendor_dashboard')
        else:
            error_message = "Invalid username or password. Please try again."
            return render(request, 'evms/vendor-login.html', {'error_message': error_message})
    else:
        return render(request, 'evms/vendor-login.html')

def vendor_logout(request):
    logout(request)
    return redirect('vendor_login')

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile

@login_required
def vendor_dashboard(request):
    if request.user.is_authenticated:
        try:
            vendor = Vendor.objects.get(user=request.user)
            referral_link = request.build_absolute_uri('/candidateform/?ref={}'.format(vendor.refer_code))
            candidates = Candidate.objects.filter(refer_code=vendor.refer_code).order_by('-id')
            num_candidates = candidates.count()

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(referral_link)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="#1A4D8F", back_color="white").convert('RGB')
            
            # Add logo if available
            try:
                logo_path = os.path.join(settings.STATIC_ROOT, 'images/logo.png')
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path)
                    qr_size = qr_img.size[0]
                    logo_size = qr_size // 4
                    logo = logo.resize((logo_size, logo_size))
                    pos = ((qr_size - logo_size) // 2, (qr_size - logo_size) // 2)
                    qr_img.paste(logo, pos)
            except Exception as e:
                print(f"Logo addition skipped: {e}")

            # Create printable image
            printable_img = Image.new('RGB', (800, 1000), color='white')
            draw = ImageDraw.Draw(printable_img)
            
            # Font handling with fallback
            try:
                font_path = os.path.join(settings.STATIC_ROOT, 'fonts/Roboto-Regular.ttf')
                font_large = ImageFont.truetype(font_path, 36)
                font_medium = ImageFont.truetype(font_path, 24)
            except:
                # Fallback to default font if Roboto not available
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                print("Using default font - Roboto not found")
            
            # Add text
            draw.text((400, 50), "Scan to Register", fill="#1A4D8F", font=font_large, anchor='mm')
            draw.text((400, 100), f"Referral Code: {vendor.refer_code}", fill="black", font=font_medium, anchor='mm')
            
            # Add QR code
            qr_img = qr_img.resize((500, 500))
            printable_img.paste(qr_img, (150, 200))
            
            # Add footer
            draw.text((400, 750), "Powered by EMTA", fill="#1A4D8F", font=font_medium, anchor='mm')
            
            # Generate plain QR code
            qr_plain = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr_plain.add_data(referral_link)
            qr_plain.make(fit=True)
            qr_img_plain = qr_plain.make_image(fill_color="black", back_color="white").convert('RGB')
            
            # Save QR with design
            buffer_with_design = BytesIO()
            printable_img.save(buffer_with_design, format='PNG')
            qr_code_file_with_design = ContentFile(buffer_with_design.getvalue(), name=f'{vendor.user.username}_qr_design.png')
            vendor.qr_code.save(qr_code_file_with_design.name, qr_code_file_with_design)
            
            # Save plain QR
            buffer_plain = BytesIO()
            qr_img_plain.save(buffer_plain, format='PNG')
            qr_code_file_plain = ContentFile(buffer_plain.getvalue(), name=f'{vendor.user.username}_qr_plain.png')
            vendor.qr_code_plain.save(qr_code_file_plain.name, qr_code_file_plain)

            # Save vendor details
            vendor.save()

            if request.method == 'POST' and request.FILES.get('profile_picture'):
                profile_picture = request.FILES['profile_picture']
                vendor.profile_image = profile_picture
                vendor.save()

            context = {
                'vendor': vendor,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'candidates': candidates,
                'num_candidates': num_candidates,
                'referral_link': referral_link,
                'qr_code_url': vendor.qr_code.url if vendor.qr_code else None,
                'qr_code_plain_url': vendor.qr_code_plain.url if vendor.qr_code_plain else None,
            }

            return render(request, 'evms/vendor-dashboard.html', context)

        except Vendor.DoesNotExist:
            return render(request, 'usernotfound.html', {'error': 'Vendor details not found'})
    else:
        return render(request, 'usernotfound.html', {'error': 'User not authenticated'})
    
def vendor_profile(request, id):
    vendor = get_object_or_404(Vendor, id=id)
    vendor_profile_detail, _ = Vendor_profile_details.objects.get_or_create(vendor=vendor)
    vendor_bussiness_detail, _ = Vendor_bussiness_details.objects.get_or_create(vendor=vendor)
    vendor_bank_detail, _ = Vendor_bank_details.objects.get_or_create(vendor=vendor)

    if request.method == 'POST':
        if 'submit_all_details' in request.POST:
            # Handle all three forms at once
            # Profile Details
            vendor.user.first_name = request.POST.get('first_name')
            vendor.user.last_name = request.POST.get('last_name')
            vendor.user.save()
            vendor.mobile_number = request.POST.get('mobile_number')
            vendor.email = request.POST.get('email')
            vendor.date_of_birth = request.POST.get('date_of_birth')
            
            if 'vendor_profile_image' in request.FILES:
                vendor.vendor_profile_image = request.FILES['vendor_profile_image']
            vendor.save()
            
            vendor_profile_detail.gender = request.POST.get('gender')
            vendor_profile_detail.address = request.POST.get('address')
            vendor_profile_detail.adhar_card_number = request.POST.get('adhar_card_number')
            vendor_profile_detail.pan_card_number = request.POST.get('pan_card_number')
            vendor_profile_detail.location = request.POST.get('location')
            
            if 'adhar_card_image' in request.FILES:
                vendor_profile_detail.adhar_card_image = request.FILES['adhar_card_image']
            if 'pan_card_image' in request.FILES:
                vendor_profile_detail.pan_card_image = request.FILES['pan_card_image']
            vendor_profile_detail.save()

            # Business Details
            vendor_bussiness_detail.shop_name = request.POST.get('shop_name')
            vendor_bussiness_detail.busness_type = request.POST.get('busness_type')
            vendor_bussiness_detail.shop_address = request.POST.get('shop_address')
            vendor_bussiness_detail.Contact_number = request.POST.get('Contact_number')
            vendor_bussiness_detail.Busness_email = request.POST.get('Busness_email')
            vendor_bussiness_detail.Gumasta_number = request.POST.get('Gumasta_number')
            vendor_bussiness_detail.gst_number = request.POST.get('gst_number')
            vendor_bussiness_detail.Bpan_number = request.POST.get('Bpan_number')
            vendor_bussiness_detail.MSME_number = request.POST.get('MSME_number')
            vendor_bussiness_detail.VCname = request.POST.get('VCname')
            vendor_bussiness_detail.VCmobile = request.POST.get('VCmobile')
            vendor_bussiness_detail.VCaddress = request.POST.get('VCaddress')
            
            if 'gumasta_image' in request.FILES:
                vendor_bussiness_detail.gumasta_image = request.FILES['gumasta_image']
            if 'gst_image' in request.FILES:
                vendor_bussiness_detail.gst_image = request.FILES['gst_image']
            if 'Bpan_image' in request.FILES:
                vendor_bussiness_detail.Bpan_image = request.FILES['Bpan_image']
            if 'MSME_image' in request.FILES:
                vendor_bussiness_detail.MSME_image = request.FILES['MSME_image']
            if 'Bphoto_outer' in request.FILES:
                vendor_bussiness_detail.Bphoto_outer = request.FILES['Bphoto_outer']
            if 'Bphoto_inside' in request.FILES:
                vendor_bussiness_detail.Bphoto_inside = request.FILES['Bphoto_inside']
            vendor_bussiness_detail.save()

            # Bank Details
            vendor_bank_detail.account_holder_name = request.POST.get('account_holder_name')
            vendor_bank_detail.bank_name = request.POST.get('bank_name')
            vendor_bank_detail.account_number = request.POST.get('account_number')
            vendor_bank_detail.ifs_code = request.POST.get('ifs_code')
            vendor_bank_detail.micr_code = request.POST.get('micr_code')
            vendor_bank_detail.account_type = request.POST.get('account_type')
            vendor_bank_detail.preffered_payout_date = request.POST.get('preffered_payout_date')
            
            if 'bank_document' in request.FILES:
                vendor_bank_detail.bank_document = request.FILES['bank_document']
            vendor_bank_detail.save()

            messages.success(request, 'All details updated successfully!')
            return redirect('vendor_profile', id=vendor.id)

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
        'districts': districts,
        # 'today': datetime.date.today().strftime('%Y-%m-%d')
    }
    return render(request, 'evms/vendor-profile.html', context)

def candidate_form(request):
    if request.method == 'POST':
        candidate_name = request.POST.get('candidate_name')
        candidate_mobile_number = request.POST.get('candidate_mobile_number')
        candidate_email_address = request.POST.get('candidate_email_address')
        qualification = request.POST.get('qualification')
        sector = request.POST.getlist('sector')
        job_type = request.POST.get('job_type')
        preferred_location = request.POST.getlist('preferred_location')
        candidate_resume = request.FILES.get('candidate_resume')
        candidate_photo = request.FILES.get('candidate_photo')
        refer_code = request.POST.get('refer_code', '')
        sector_str = ', '.join(sector)
        preferred_location_str = ', '.join(preferred_location)
        
        # Check if candidate already exists
        candidate = Candidate.objects.filter(
            candidate_mobile_number=candidate_mobile_number
        ).first()

        if candidate:
            # If existing candidate has no refer_code, update it
            if not candidate.refer_code and refer_code:
                candidate.refer_code = refer_code
                candidate.save()
            
            messages.error(request, "A profile with this mobile number already exists.")
            return render(request, 'evms/candidate-apply-form.html', {'initial_data': {'refer_code': refer_code}})
        else:
            # If no existing candidate, proceed to create a new one
            candidate = Candidate.objects.create(
                candidate_name=candidate_name,
                qualification=qualification,
                candidate_mobile_number=candidate_mobile_number,
                candidate_email_address=candidate_email_address,
                candidate_resume=candidate_resume,
                sector=sector_str,
                preferred_location=preferred_location_str,
                refer_code=refer_code,
                job_type=job_type,
                candidate_photo=candidate_photo,
            )

            # return redirect(CandidateSuccess, candidate_id=candidate.id)
            return redirect ('thankyou')

    else:
        refer_code = request.GET.get('ref', '')
        initial_data = {'refer_code': refer_code}
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
        return render(request, 'evms/candidate-apply-form.html', {'initial_data': initial_data,'job_sectors':job_sectors,'districts':districts})
    
def term_and_conditions(request) :
    return render (request,'evms/candidate-t&c.html')

def thankyou(request) :
    return render (request,'evms/thankyou.html')

import os
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import default_storage
from .models import Candidate, Vendor

def bulk_upload_candidates(request):
    vendor = Vendor.objects.get(user=request.user)
    duplicate_candidates = []  # Store duplicate candidate data

    if request.method == "POST" and request.FILES.get("excel_file"):
        if 'submit_vendor_profile_details' in request.POST:
            excel_file = request.FILES["excel_file"]

        # Save the file temporarily
        file_path = default_storage.save("temp/" + excel_file.name, excel_file)
        full_path = os.path.join(default_storage.location, file_path)

        try:
            # Read Excel File
            df = pd.read_excel(full_path, engine="openpyxl")
            required_columns = [
                "candidate_name", "candidate_mobile_number", "candidate_email_address",
                "qualification", "sector", "job_type", "preferred_location",
                "refer_code"
            ]

            # Validate required columns
            if not all(col in df.columns for col in required_columns):
                messages.error(request, "Invalid Excel format. Please use the sample template.")
                return redirect("bulk_upload_candidates")

            created_count = 0
            duplicate_count = 0

            for _, row in df.iterrows():
                mobile_number = str(row["candidate_mobile_number"]).strip()
                email_address = str(row["candidate_email_address"]).strip()

                # Check for duplicates
                existing_candidate = Candidate.objects.filter(
                    candidate_mobile_number=mobile_number
                ).first() or Candidate.objects.filter(
                    candidate_email_address=email_address
                ).first()

                if existing_candidate:
                    duplicate_candidates.append({
                        "candidate_name": row["candidate_name"],
                        "candidate_mobile_number": mobile_number,
                        "candidate_email_address": email_address,
                        "qualification": row["qualification"],
                        "sector": row["sector"],
                        "job_type": row["job_type"],
                        "preferred_location": row["preferred_location"],
                        "refer_code": row.get("refer_code", ""),
                    })
                    duplicate_count += 1
                    continue

                # Create candidate record
                Candidate.objects.create(
                    candidate_name=row["candidate_name"],
                    candidate_mobile_number=mobile_number,
                    candidate_email_address=email_address,
                    qualification=row["qualification"],
                    sector=row["sector"],
                    job_type=row["job_type"],
                    preferred_location=row["preferred_location"],
                    refer_code=row.get("refer_code", ""),
                )
                created_count += 1

            # Success Message
            messages.success(request, f"Successfully added {created_count} candidates. {duplicate_count} duplicates skipped.")

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")

        finally:
            # Clean up the temporary file
            os.remove(full_path)

    return render(request, "evms/candidate-bulk-upload.html", {
        'vendor': vendor,
        'duplicate_candidates': duplicate_candidates  # Pass duplicates to template
    })


def download_sample_excel(request):
    refer_code = request.GET.get("refer_code", "YOUR_REF_CODE")

    data = {
        "candidate_name": ["John Doe"],
        "candidate_mobile_number": ["9876543210"],
        "candidate_email_address": ["johndoe@example.com"],
        "qualification": ["MBA"],
        "sector": ["Banking, Insurance"],
        "job_type": ["Full-Time"],
        "preferred_location": ["Mumbai, Delhi"],
        "refer_code": [refer_code],
    }

    df = pd.DataFrame(data)

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="Candidate_Sample.xlsx"'
    
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    return response



from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Candidate
from django.db.models import Sum

def revenue_data(request):
    vendor = Vendor.objects.get(user=request.user)
    # Get filter parameter
    days = int(request.GET.get('days', 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Filter candidates by selection date range
    candidates = Candidate.objects.filter(
        commission_generation_date__isnull=False,
        vendor_commission__isnull=False,
        commission_generation_date__gte=start_date,
        commission_generation_date__lte=end_date,
        refer_code = vendor.refer_code
    )
    
    # Calculate total commission
    total_commission = candidates.aggregate(
        total=Sum('vendor_commission')
    )['total'] or 0
    
    # Calculate growth percentage (simplified example)
    prev_period_total = Candidate.objects.filter(
        commission_generation_date__gte=start_date - timedelta(days=days),
        commission_generation_date__lt=start_date,
        vendor_commission__isnull=False,
    ).aggregate(
        total=Sum('vendor_commission')
    )['total'] or 0
    
    growth_percentage = 0
    if prev_period_total > 0:
        growth_percentage = round(((total_commission - prev_period_total) / prev_period_total) * 100, 1)
    
    # Prepare chart data (group by day)
    chart_data = []
    current_date = start_date
    while current_date <= end_date:
        daily_total = Candidate.objects.filter(
            commission_generation_date=current_date,
            vendor_commission__isnull=False,
            refer_code = vendor.refer_code
        ).aggregate(
            total=Sum('vendor_commission')
        )['total'] or 0
        
        chart_data.append({
            'x': current_date.isoformat(),
            'y': float(daily_total)
        })
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'total_commission': total_commission,
        'growth_percentage': growth_percentage,
        'chart_data': chart_data
    })
    
    

def candidate_profile_details(request, id) :
    vendor = Vendor.objects.get(user=request.user)
    candidate = get_object_or_404(Candidate, id=id)
    context = {
        'candidate': candidate,
        'vendor': vendor,
    }
    return render(request, 'evms/candidate-profile-details.html', context)

def vendor_selected_candidate(request) :
    vendor = Vendor.objects.get(user=request.user)
    candidates = Candidate.objects.filter(vendor_commission__isnull=False,refer_code=vendor.refer_code).order_by('-id')
    num_selected_candidate = candidates.count()
    
    context = {
        'candidates': candidates,
        'vendor': vendor,
        'num_selected_candidate' : num_selected_candidate
    }
    return render(request, 'evms/vendor-selected-candidate.html', context)

def vendor_transaction_history(request) :
    vendor = Vendor.objects.get(user=request.user)
    candidates = Candidate.objects.filter(
        vendor_commission__isnull=False,
        refer_code=vendor.refer_code,
        vendor_commission_status__in=['Success', 'Complete', 'Pending', 'Failed']
    ).order_by('-id')
    
    context = {
        'vendor' : vendor,
        'candidates' : candidates
    }
    return render (request, 'evms/transaction-history.html', context)