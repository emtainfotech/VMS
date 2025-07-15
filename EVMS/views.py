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
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import random
import time
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from .models import Vendor
from django.http import HttpResponseForbidden

def home_view(request):
    return render(request, 'evms/home.html', {})

def sitemap_view(request) :
    return render(request, 'evms/sitemap.xml', {})

def robot_txt_view(request) :
    return render(request, 'evms/robots.txt', {})


def vendor_signup(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        # Initial signup form submission
        if form_type == 'signup':
            # Validate form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            mobile_number = request.POST.get('mobile_number')
            email = request.POST.get('email')
            username = request.POST.get('username')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # Basic validation
            errors = []
            if not username:
                errors.append('Username must be set')
            if password1 != password2:
                errors.append('Passwords do not match')
            if User.objects.filter(username=username).exists():
                errors.append('Username is already taken')
            if User.objects.filter(email=email).exists():
                errors.append('Email is already taken')
            # First name validation
            if not first_name or not first_name.isalpha() or len(first_name) > 30:
                errors.append('First name is required and should contain only letters (max 30 characters).')
            # Last name validation (optional, but if present, only letters)
            if last_name and (not last_name.isalpha() or len(last_name) > 30):
                errors.append('Last name should contain only letters (max 30 characters).')
            # Mobile number validation
            if not mobile_number or not mobile_number.isdigit() or len(mobile_number) != 10:
                errors.append('Mobile number is required and must be 10 digits.')
            elif Vendor.objects.filter(mobile_number=mobile_number).exists():
                errors.append('Mobile number is already registered.')
            # Email validation
            email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
            if not email or not re.match(email_regex, email):
                errors.append('A valid email address is required.')
            elif User.objects.filter(email=email).exists():
                errors.append('Email is already taken')
            # Username validation
            if not username or len(username) < 4 or len(username) > 30 or ' ' in username:
                errors.append('Username is required, must be 4-30 characters, and contain no spaces.')
            elif User.objects.filter(username=username).exists():
                errors.append('Username is already taken')
            # Password validation
            if not password1 or len(password1) < 8:
                errors.append('Password must be at least 8 characters long.')
            if password1 != password2:
                errors.append('Passwords do not match')
            
            if errors:
                return JsonResponse({
                    'status': 'error',
                    'messages': errors
                }, status=400)
            
            # Store data in session for OTP verification
            request.session['signup_data'] = {
                'first_name': first_name,
                'last_name': last_name,
                'mobile_number': mobile_number,
                'email': email,
                'username': username,
                'password1': password1,
                'refer_code': username
            }
            
            # Generate and store OTP (6 digits)
            otp = str(random.randint(100000, 999999))
            request.session['signup_otp'] = otp
            request.session['otp_email'] = email
            request.session['otp_attempts'] = 0  # Track OTP attempts
            request.session['otp_created_at'] = time.time()  # Current timestamp
            
            # Send OTP email
            try:
                send_otp_email(email, otp)
                return JsonResponse({
                    'status': 'success',
                    'message': 'OTP sent to your email'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to send OTP. Please try again.'
                }, status=500)
        
        # OTP verification submission
        elif form_type == 'otp_verification':
            # Verify OTP from session
            stored_otp = request.session.get('signup_otp')
            user_otp = ''.join([
                request.POST.get('otp1', ''),
                request.POST.get('otp2', ''),
                request.POST.get('otp3', ''),
                request.POST.get('otp4', ''),
                request.POST.get('otp5', ''),
                request.POST.get('otp6', '')
            ])
            
            # Check if OTP matches
            if stored_otp and user_otp == stored_otp:
                signup_data = request.session.get('signup_data')
                
                # Create user account
                user = User.objects.create_user(
                    username=signup_data['username'],
                    email=signup_data['email'],
                    password=signup_data['password1']
                )
                user.first_name = signup_data['first_name']
                user.last_name = signup_data['last_name']
                user.save()
                
                # Create vendor profile
                vendor = Vendor.objects.create(
                    user=user,
                    mobile_number=signup_data['mobile_number'],
                    refer_code=signup_data['refer_code']
                )
                
                # Send welcome email
                try:
                    send_welcome_email(signup_data)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send welcome email: {str(e)}")
                
                # Clear session data
                clear_signup_session(request)
                
                return JsonResponse({
                    'status': 'success',
                    'redirect': reverse('vendor_login'),
                    'message': 'Registration successful! Please login.'
                })
            else:
                # Track failed attempts
                request.session['otp_attempts'] = request.session.get('otp_attempts', 0) + 1
                
                # Prevent brute force (max 5 attempts)
                if request.session['otp_attempts'] >= 5:
                    clear_signup_session(request)
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Too many failed attempts. Please restart registration.',
                        'redirect': reverse('vendor_signup')
                    }, status=400)
                
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid OTP. Please try again.'
                }, status=400)
    
    # GET request - show initial form
    suggested_username = get_next_username()
    return render(request, 'evms/vendor-signup.html', {
        'suggested_username': suggested_username
    })

@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        email = request.session.get('otp_email')
        
        if email:
            # Generate new OTP
            otp = str(random.randint(100000, 999999))
            request.session['signup_otp'] = otp
            request.session['otp_created_at'] = time.time()
            
            # Resend email
            try:
                send_otp_email(email, otp)
                return JsonResponse({
                    'status': 'success',
                    'message': 'New OTP sent successfully'
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to resend OTP. Please try again.'
                }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Unable to resend OTP. Please restart registration.'
    }, status=400)

# Helper Functions

def send_otp_email(email, otp):
    subject = 'Your EMTA VMS Verification Code'
    message = f"""
    Your OTP for EMTA VMS registration is: {otp}
    
    This code will expire in 10 minutes.
    
    If you didn't request this, please ignore this email.
    """
    send_mail(
        subject,
        message.strip(),
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

def send_welcome_email(vendor_data):
    subject = 'Welcome to EMTA Vendor Management System'
    
    context = {
        'first_name': vendor_data['first_name'],
        'last_name': vendor_data['last_name'],
        'username': vendor_data['username'],
        'email': vendor_data['email'],
        'mobile_number': vendor_data['mobile_number'],
        'refer_code': vendor_data['refer_code'],
        'refer_code': vendor_data['refer_code'],
        'company_name': 'EMTA VMS',
        'company_info': 'EMTA Vendor Management System provides comprehensive solutions for vendor onboarding and management.',
        'support_email': 'marketing.emta02@gmail.com',
        'website': 'www.emtavms.com',
    }

    html_message = render_to_string('emails/vendor_welcome.html', context)
    plain_message = render_to_string('emails/vendor_welcome.txt', context)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [vendor_data['email']],
        html_message=html_message,
        fail_silently=False,
    )

def clear_signup_session(request):
    """Clear all signup-related session data"""
    keys = ['signup_data', 'signup_otp', 'otp_email', 'otp_attempts', 'otp_created_at']
    for key in keys:
        if key in request.session:
            del request.session[key]

def get_next_username():
    # Get all usernames that start with 'EMTA' and end with 5 digits
    users = User.objects.filter(username__regex=r'^EMTA\d{5}$').values_list('username', flat=True)

    # Extract the numeric part from each username
    numbers = [int(re.search(r'\d{5}', username).group()) for username in users]

    if numbers:
        next_number = max(numbers) + 1  # Increment the max number found
    else:
        next_number = 1  # Start with EMTA00001 if no usernames exist

    # Format the next username with leading zeros (e.g., EMTA00001)
    return f"EMTA{next_number:05d}"

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

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import random
import time
from .models import Vendor  # Assuming you have a Vendor model

def forgot_password(request):
    if request.method == 'POST':
        try:
            email_or_mobile = request.POST.get('email_or_mobile', '').strip()
            
            if not email_or_mobile:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email or mobile number is required'
                }, status=400)
            
            # Check if input is email or mobile
            if '@' in email_or_mobile:  # Email
                try:
                    user = User.objects.get(email=email_or_mobile)
                    email = user.email
                except User.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No account found with this email'
                    }, status=400)
            else:  # Mobile
                try:
                    vendor = Vendor.objects.get(mobile_number=email_or_mobile)
                    email = vendor.user.email
                    user = vendor.user
                except Vendor.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No account found with this mobile number'
                    }, status=400)
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            request.session['reset_user_id'] = user.id
            request.session['otp_created_at'] = time.time()
            request.session['otp_attempts'] = 0
            
            # Send email
            subject = 'Password Reset OTP'
            message = f'Your OTP for password reset is: {otp}\nThis OTP is valid for 10 minutes.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'OTP sent to your registered email'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return render(request, 'evms/forgot_password.html')

@csrf_exempt
def reset_password_otp(request):
    if request.method == 'POST':
        try:
            # Debugging - print session data
            print("Session OTP:", request.session.get('reset_otp'))
            print("Session User ID:", request.session.get('reset_user_id'))
            
            # Get OTP from request
            otp_data = {
                'otp1': request.POST.get('otp1', ''),
                'otp2': request.POST.get('otp2', ''),
                'otp3': request.POST.get('otp3', ''),
                'otp4': request.POST.get('otp4', ''),
                'otp5': request.POST.get('otp5', ''),
                'otp6': request.POST.get('otp6', '')
            }
            print("Received OTP data:", otp_data)
            
            user_otp = ''.join([otp_data[f'otp{i}'] for i in range(1, 7)])
            stored_otp = request.session.get('reset_otp')
            user_id = request.session.get('reset_user_id')
            
            if not (stored_otp and user_id):
                return JsonResponse({
                    'status': 'error',
                    'message': 'OTP session expired. Please try again.'
                }, status=400)
            
            # Check OTP expiration (10 minutes)
            if time.time() - request.session.get('otp_created_at', 0) > 600:
                clear_reset_session(request)
                return JsonResponse({
                    'status': 'error',
                    'message': 'OTP expired. Please request a new one.'
                }, status=400)
            
            if user_otp == stored_otp:
                request.session['otp_verified'] = True
                return JsonResponse({
                    'status': 'success',
                    'redirect': reverse('reset_password_form')
                })
            else:
                request.session['otp_attempts'] = request.session.get('otp_attempts', 0) + 1
                print(f"OTP mismatch. Stored: {stored_otp}, Received: {user_otp}")
                
                if request.session['otp_attempts'] >= 5:
                    clear_reset_session(request)
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Too many failed attempts. Please start again.'
                    }, status=400)
                
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid OTP. Please try again.'
                }, status=400)
                
        except Exception as e:
            print("Error in OTP verification:", str(e))
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred. Please try again.'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

def reset_password_form(request):
    if not request.session.get('otp_verified'):
        return redirect('forgot_password')
    
    if request.method == 'POST':
        try:
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            user_id = request.session.get('reset_user_id')
            
            if password1 != password2:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match'
                }, status=400)
            
            if len(password1) < 8:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Password must be at least 8 characters'
                }, status=400)
            
            user = User.objects.get(id=user_id)
            user.set_password(password1)
            user.save()
            
            clear_reset_session(request)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Password reset successfully!',
                'redirect': reverse('vendor_login')
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return render(request, 'evms/reset_password.html')

@csrf_exempt
def resend_reset_otp(request):
    if request.method == 'POST':
        try:
            email = request.session.get('reset_email')
            
            if not email:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Session expired'
                }, status=400)
            
            otp = str(random.randint(100000, 999999))
            request.session['reset_otp'] = otp
            request.session['otp_created_at'] = time.time()
            
            subject = 'Password Reset OTP'
            message = f'Your new OTP is: {otp}\nThis OTP is valid for 10 minutes.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'New OTP sent successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    }, status=400)

def clear_reset_session(request):
    keys = ['reset_otp', 'reset_email', 'reset_user_id', 
            'otp_created_at', 'otp_attempts', 'otp_verified']
    for key in keys:
        if key in request.session:
            del request.session[key]
            
            
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
            referral_link = request.build_absolute_uri('/applicationform/?ref={}'.format(vendor.refer_code))
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
            
            referal_poster = Referal_poster.objects.first() 
            

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
                'referal_poster' : referal_poster,
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
            vendor.mobile_number = request.POST.get('mobile_number')
            vendor.user.email = request.POST.get('email')
            vendor.date_of_birth = request.POST.get('date_of_birth')
            vendor.user.save()
            
            if 'vendor_profile_image' in request.FILES:
                vendor.vendor_profile_image = request.FILES['vendor_profile_image']
            vendor.save()
            
            vendor_profile_detail.gender = request.POST.get('gender')
            vendor_profile_detail.address = request.POST.get('address')
            vendor_profile_detail.adhar_card_number = request.POST.get('adhar_card_number')
            vendor_profile_detail.pan_card_number = request.POST.get('pan_card_number')
            vendor_profile_detail.location = request.POST.get('location')
            vendor_profile_detail.pin_code = request.POST.get('pin_code')
            vendor_profile_detail.other_location = request.POST.get('other_location')
            
            if 'adhar_card_image' in request.FILES:
                vendor_profile_detail.adhar_card_image = request.FILES['adhar_card_image']
            if 'pan_card_image' in request.FILES:
                vendor_profile_detail.pan_card_image = request.FILES['pan_card_image']
            vendor_profile_detail.save()

            # Business Details
            vendor_bussiness_detail.shop_name = request.POST.get('shop_name')
            vendor_bussiness_detail.busness_type = request.POST.get('busness_type')
            vendor_bussiness_detail.shop_address = request.POST.get('shop_address')
            vendor_bussiness_detail.shop_location = request.POST.get('shop_location')
            vendor_bussiness_detail.shop_pin_code = request.POST.get('shop_pin_code')
            vendor_bussiness_detail.shop_other_location = request.POST.get('shop_other_location')
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

    
        
        # Server-side validation
        errors = []
        import re
        # Candidate name: required, only letters and spaces
        if not candidate_name or not re.match(r'^[A-Za-z ]+$', candidate_name) or len(candidate_name) > 50:
            errors.append('Candidate name is required and should contain only letters and spaces (max 50 characters).')
        # Mobile number: required, only digits, exactly 10
        if not candidate_mobile_number or not candidate_mobile_number.isdigit() or len(candidate_mobile_number) != 10:
            errors.append('Mobile number is required and must be exactly 10 digits.')
        # Email: required, valid format
        email_regex = r'^([\w\.-]+)@([\w\.-]+)\.([a-zA-Z]{2,})$'
        if not candidate_email_address or not re.match(email_regex, candidate_email_address):
            errors.append('A valid email address is required.')
        # Qualification: required
        if not qualification:
            errors.append('Qualification is required.')
        # Sector: required
        if not sector:
            errors.append('At least one sector must be selected.')
        # Job type: required
        if not job_type:
            errors.append('Job type is required.')
        # Preferred location: required
        if not preferred_location:
            errors.append('At least one preferred location must be selected.')
        # Resume: required
        if not candidate_resume:
            errors.append('Candidate resume is required.')
        # Photo: required
        if not candidate_photo:
            errors.append('Candidate photo is required.')

        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'evms/candidate-apply-form.html', {'initial_data': {'refer_code': refer_code}})
        
        

        # Get all employees for round robin assignment
        employees = Employee.objects.all()
        if employees.exists():
            # Get the last assigned employee's ID from session or default to 0
            last_employee_id = request.session.get('last_assigned_employee_id', 0)
            
            # Find the next employee in round robin fashion
            next_employee = employees.filter(id__gt=last_employee_id).first()
            if not next_employee:
                next_employee = employees.first()
            
            # Update the session with the new last assigned employee ID
            request.session['last_assigned_employee_id'] = next_employee.id
            
            # Get the employee's full name
            employee_name = f"{next_employee.first_name} {next_employee.last_name} ({next_employee.employee_id})"
        else:
            employee_name = "Unassigned"
        
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
                employee_name=employee_name,  # Add the assigned employee name
            )
        
            # Send confirmation email to candidate
            try:
                subject = 'Application Received - EMTA VMS'
                
                context = {
                    'candidate_name': candidate_name,
                    'qualification': qualification,
                    'sector': sector_str,
                    'job_type': job_type,
                    'preferred_location': preferred_location_str,
                    'refer_code': refer_code,
                    'support_email': 'marketing.emta02@gmail.com',
                    'company_name': 'EMTA VMS',
                }

                html_message = render_to_string('emails/candidate_confirmation.html', context)
                plain_message = render_to_string('emails/candidate_confirmation.txt', context)

                send_mail(
                    subject,
                    plain_message,
                    'marketing.emta02@gmail.com',
                    [candidate_email_address],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                # Log error but don't break the flow
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send candidate confirmation email: {str(e)}")

            return redirect('thankyou')
        
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
                "candidate_name", "candidate_mobile_number","alternate_mobile_number", "candidate_email_address",
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
                alternate_mobile_number = str(row["alternate_mobile_number"]).strip()
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
                        "alternate_mobile_number": alternate_mobile_number,
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
                    alternate_mobile_number=alternate_mobile_number,
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
        "alternate_mobile_number": ["9123456780"],
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

from django.template.loader import render_to_string
from django.http import HttpResponse
from datetime import datetime
from xhtml2pdf import pisa
from io import BytesIO

def generate_vendor_invoice(request, candidate_id):
    # Get candidate and related vendor details
    candidate = Candidate.objects.get(pk=candidate_id)
    vendor = Vendor.objects.get(refer_code=candidate.refer_code)
    
    # Get all related vendor details
    try:
        profile_details = Vendor_profile_details.objects.get(vendor=vendor)
    except Vendor_profile_details.DoesNotExist:
        profile_details = None
    
    try:
        business_details = Vendor_bussiness_details.objects.get(vendor=vendor)
    except Vendor_bussiness_details.DoesNotExist:
        business_details = None
    
    try:
        bank_details = Vendor_bank_details.objects.get(vendor=vendor)
    except Vendor_bank_details.DoesNotExist:
        bank_details = None
    
    # Prepare context data
    context = {
        # Invoice metadata
        'invoice_number': f"INV-{datetime.now().strftime('%Y%m%d')}-{candidate.unique_id}",
        'invoice_date': datetime.now().strftime('%d %b %Y'),
        'due_date': candidate.vendor_payout_date.strftime('%d %b %Y') if candidate.vendor_payout_date else '',
        
        # Vendor details
        'vendor': {
            'name': vendor.user.get_full_name(),
            'code': vendor.refer_code,
            'mobile': vendor.mobile_number,
            'email': vendor.user.email,
            'total_commission': vendor.total_commission_received,
        },
        
        # Vendor profile details
        'vendor_profile': {
            'address': profile_details.address if profile_details else '',
            'gender': profile_details.gender if profile_details else '',
            'aadhar': profile_details.adhar_card_number if profile_details else '',
            'pan': profile_details.pan_card_number if profile_details else '',
        } if profile_details else None,
        
        # Business details
        'business': {
            'name': business_details.shop_name if business_details else '',
            'address': business_details.shop_address if business_details else '',
            'type': business_details.busness_type if business_details else '',
            'gst': business_details.gst_number if business_details else '',
            'contact': business_details.Contact_number if business_details else '',
            'email': business_details.Busness_email if business_details else '',
        } if business_details else None,
        
        # Bank details
        'bank': {
            'account_holder': bank_details.account_holder_name if bank_details else '',
            'account_number': bank_details.account_number if bank_details else '',
            'bank_name': bank_details.bank_name if bank_details else '',
            'ifsc': bank_details.ifs_code if bank_details else '',
            'preferred_payout': bank_details.preffered_payout_date if bank_details else '',
        } if bank_details else None,
        
        # Candidate details
        'candidate': {
            'name': candidate.candidate_name,
            'code': candidate.unique_id,
            'mobile': candidate.candidate_mobile_number,
            'email': candidate.candidate_email_address,
            'position': candidate.job_type,
            'department': candidate.department,
            'company': candidate.company_name,
            'selection_date': candidate.selection_date.strftime('%d %b %Y') if candidate.selection_date else '',
            'joining_date': candidate.candidate_joining_date if candidate.candidate_joining_date else '',
            'offered_salary': candidate.offered_salary,
            'experience': f"{candidate.experience_year} years {candidate.experience_month} months",
        },
        
        # Commission details
        'commission': {
            'amount': candidate.vendor_commission,
            'status': candidate.vendor_commission_status,
            'generation_date': candidate.commission_generation_date.strftime('%d %b %Y') if candidate.commission_generation_date else '',
            'payout_date': candidate.vendor_payout_date.strftime('%d %b %Y') if candidate.vendor_payout_date else '',
            'remark': candidate.vendor_payment_remark,
            'emta_commission': candidate.emta_commission,
        },
        
        # Selection status
        'selection': {
            'status': candidate.selection_status,
            'company': candidate.company_name,
            'call_remark': candidate.calling_remark,
            'lead_source': candidate.lead_source,
            'submitted_by': candidate.submit_by,
        },
        
        # Additional fields
        'current_date': datetime.now().strftime('%d %b %Y'),
    }
    
    # Render HTML template
    html_string = render_to_string('evms/vendor_invoice.html', context)
    
    # Create PDF using xhtml2pdf
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Vendor_Invoice_{candidate.unique_id}.pdf"'
        return response
    
    return HttpResponse("Error generating PDF", status=500)

def notifications(request):
    if request.user.is_authenticated and hasattr(request.user, 'vendor'):
        return {
            'notifications': request.user.vendor.notifications.filter(is_read=False)[:10],
            'unread_count': request.user.vendor.notifications.filter(is_read=False).count()
        }
    return {'notifications': [], 'unread_count': 0}

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, vendor=request.user.vendor)
    notification.is_read = True
    notification.save()
    return redirect(notification.url if notification.url else 'dashboard')

@login_required
def mark_all_notifications_read(request):
    request.user.vendor.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def refer_poster_vendor_view(request):
    poster = Referal_poster.objects.first()  # Only one poster should exist

    if request.method == 'POST':
        referal_image = request.FILES.get('referal_image')
        if referal_image:
            # Delete old image if exists
            if poster:
                # Delete file from storage
                if poster.referal_image and os.path.isfile(poster.referal_image.path):
                    os.remove(poster.referal_image.path)
                # Delete the record
                poster.delete()

            # Create new poster
            new_poster = Referal_poster.objects.create(referal_image=referal_image)
            messages.success(request, 'Referral poster uploaded successfully')
            return redirect('refer_poster_vendor_view')  # Redirect to prevent re-submission

    # Get the current poster again in case it was updated
    poster = Referal_poster.objects.first()
    return render(request, 'evms/referal-poster.html', {'poster': poster})


