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
from .utils import convert_number_to_words
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


IST = pytz.timezone('Asia/Kolkata')

def mark_notifications_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))


def custom_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("dashboard")  
        else:
            messages.error(request, "Invalid credentials or insufficient permissions.")
    return render(request, "hrms/admin-login.html")

def admin_signup_view(request):
    if request.method == 'POST':
        # Capture form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        is_admin = request.POST.get('is_admin')  # Check if admin checkbox is checked
        
        # Password validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'hrms/admin-signup.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'hrms/admin-signup.html')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)

        # If the checkbox is checked, make the user an admin
        if is_admin:
            user.is_superuser = True
            user.is_staff = True
            user.save()

        messages.success(request, "Admin account created successfully!")
        return redirect('custom_admin_login')  

    return render(request, 'hrms/admin-signup.html')

def home(request):
    if request.user.is_staff or request.user.is_superuser:
        Ajj = datetime.today().date()
        today = localtime().date()
        today1 = date.today()
        start_of_month = today.replace(day=1)
        meetings = Meeting.objects.filter(date=Ajj)
        leaverequests = LeaveRequest.objects.filter(status='Approved', start_date=today)
        office_expenses = OfficeExpense.objects.filter(purchase_date=today).order_by('-id')
        leaves = LeaveRequest.objects.filter(status='Hold').order_by('-id')
        employee_count = Employee.objects.all().count()
        tasks = Task.objects.all().order_by('-id')
        selected_candidates = Candidate_registration.objects.filter(
            selection_status__in=['Selected', 'Pending', 'Rejected'], register_time__date=today1
        ).order_by('-id')
        total_call_count = Candidate_registration.objects.filter(register_time__date=today1).count()
        total_connected_call = Candidate_registration.objects.filter(call_connection='Yes', register_time__date=today1).count()
        total_lead_generate = Candidate_registration.objects.filter(lead_generate='Yes', register_time__date=today1).count()
        total_placement = Candidate_registration.objects.filter(selection_status='Selected', register_time__date=today1).count()
        month_total_placement = Candidate_registration.objects.filter(
            selection_status='Selected', register_time__date__gte=start_of_month, register_time__date__lte=today
        ).count()
        todays_earning = Candidate_registration.objects.filter(register_time__date=today1).aggregate(
            total_earning=Sum('emta_commission', output_field=models.FloatField())
        )['total_earning'] or 0.0
        monthly_earning = Candidate_registration.objects.filter(
            register_time__date__gte=start_of_month, register_time__date__lte=today
        ).aggregate(
            total_earning=Sum('emta_commission', output_field=models.FloatField())
        )['total_earning'] or 0.0

        # Query sessions for today
        sessions = EmployeeSession.objects.filter(
            login_time__date=today,
            login_time__gte=datetime.combine(today, time(9, 30)),  # After 9:30 AM
            login_time__lte=datetime.combine(today, time(20, 0))  # Before 8:00 PM
        )

        session_data = []
        total_time_today = timedelta(0)  # Initialize total time for all employees

        # Get distinct users (employees)
        employees = EmployeeSession.objects.values('user').distinct()

            # Inside the loop where you process each employee
        for employee in employees:
            # Filter sessions for the current employee
            employee_sessions = sessions.filter(user_id=employee['user'])

            # Calculate total login time for the employee by summing up all session durations
            total_time = timedelta(0)
            for session in employee_sessions:
                if session.logout_time:
                    session_duration = session.logout_time - session.login_time
                else:
                    # If no logout time, assume the session is ongoing; calculate up to now
                    session_duration = now() - session.login_time
                total_time += session_duration

            # Convert total_time to hours and minutes for display
            hours = total_time.seconds // 3600
            minutes = (total_time.seconds % 3600) // 60

            # Fetch the employee object safely using .first() to avoid DoesNotExist error
            employee_obj = Employee.objects.filter(user_id=employee['user']).first()

            # Check if employee_obj exists, and only then access its properties
            if employee_obj:
                session_data.append({
                    'user_id': employee['user'],
                    'name': employee_obj.user.username,  # Employee username
                    'total_time': f"{hours}h {minutes}m"  # Total login time for the employee
                })
            else:
                # Handle case where the employee object is not found
                session_data.append({
                    'user_id': employee['user'],
                    'name': 'Unknown',  # Handle missing employee
                    'total_time': f"{hours}h {minutes}m"
                })

            # Add to the overall total time for all employees
            total_time_today += total_time


        # Convert total_time_today to hours and minutes for display
        total_hours = total_time_today.seconds // 3600
        total_minutes = (total_time_today.seconds % 3600) // 60
        total_time_str = f"{total_hours}h {total_minutes}m"

        return render(request, 'hrms/home.html', {
            'sessions': session_data,  # Employee session data
            'total_time_today': total_time_str,  # Total login time for all employees
            'meetings': meetings,
            'leaverequests': leaverequests,
            'office_expenses': office_expenses,
            'leaves': leaves,
            'employee_count': employee_count,
            'tasks': tasks,
            'selected_candidates': selected_candidates,
            'total_call_count': total_call_count,
            'total_connected_call': total_connected_call,
            'total_lead_generate': total_lead_generate,
            'total_placement': total_placement,
            'todays_earning': todays_earning,
            'monthly_earning': monthly_earning,
            'month_total_placement': month_total_placement,
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)



def employee_attendence_details(request, user_id):
    if request.user.is_staff or request.user.is_superuser:
        today = localtime().date()

        # Fetch the date range from the request, if provided
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date = None
        else:
            start_date = end_date = None

        # Filter sessions based on the date range or default to today's date
        if start_date and end_date:
            sessions = EmployeeSession.objects.filter(
                user_id=user_id, 
                login_time__date__range=(start_date, end_date)
            )
        else:
            sessions = EmployeeSession.objects.filter(
                user_id=user_id, 
                login_time__date=today
            )

        # Compute total login time for the filtered sessions
        total_time = timedelta()
        session_data = []
        for session in sessions.order_by('-id'):
            session_duration = session.total_time or timedelta()
            total_time += session_duration
            session_data.append({
                "login_time": localtime(session.login_time).strftime('%Y-%m-%d %H:%M:%S'),
                "logout_time": localtime(session.logout_time).strftime('%Y-%m-%d %H:%M:%S') if session.logout_time else "Automatically Logged Out",
                "total_time": str(session_duration) if session_duration else "N/A",
            })

        # Format total login time
        hours, remainder = divmod(total_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        total_login_time_formatted = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        # Fetch daily summary
        daily_summary = (
            EmployeeSession.objects.filter(user_id=user_id)
            .values('login_time__date')
            .annotate(
                first_login=Min('login_time'),
                last_login=Max('logout_time'),
                total_time=Sum('total_time')
            )
            .order_by('login_time__date')
        )

        day_summary = []
        for record in daily_summary:
            day_summary.append({
                "date": record['login_time__date'],
                "first_login": localtime(record['first_login']).strftime('%Y-%m-%d %H:%M:%S') if record['first_login'] else "N/A",
                "last_login": localtime(record['last_login']).strftime('%Y-%m-%d %H:%M:%S') if record['last_login'] else "N/A",
                "total_time": str(record['total_time']) if record['total_time'] else "N/A",
            })

        # Fetch monthly summary
        monthly_summary = (
            EmployeeSession.objects.filter(user_id=user_id)
            .values('login_time__year', 'login_time__month')
            .annotate(
                total_time=Sum('total_time')
            )
            .order_by('login_time__year', 'login_time__month')
        )

        month_summary = []
        for record in monthly_summary:
            month_name = datetime(record['login_time__year'], record['login_time__month'], 1).strftime('%B %Y')
            month_summary.append({
                "month": month_name,
                "total_time": str(record['total_time']) if record['total_time'] else "N/A",
            })

        return render(request, 'hrms/employee_attendence_details.html', {
            "today_sessions": session_data,
            "total_login_time_today": total_login_time_formatted,
            "daily_summary": day_summary,
            "monthly_summary": month_summary,
            "start_date": start_date,
            "end_date": end_date,
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def employee_view(request):
    if request.user.is_staff or request.user.is_superuser:
        employees = Employee.objects.all()
        socials = EmployeeSocialMedia.objects.all()
        designations = Designation.objects.all()

        if request.method == 'POST':
            # Capture form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            contact_number = request.POST.get('contact_number')
            email = request.POST.get('email')
            username = request.POST.get('username')
            employee_id = request.POST.get('employee_id')
            password = request.POST.get('password')
            address = request.POST.get('address')
            designation = request.POST.get('designation')
            joining_date = request.POST.get('joining_date')
            employee_photo = request.FILES.get('employee_photo')
            is_admin = request.POST.get('is_admin') 

            # Validate form fields (check for empty or missing fields)
            if not first_name or not last_name or not email or not username or not password:
                return render(request, 'hrms/employee.html', {'error': 'Please fill in all required fields','employees': employees, 'socials': socials, 'designations': designations})

            # Check if the username or email already exists in User model
            if User.objects.filter(username=username).exists():
                return render(request, 'hrms/employee.html', {'error': 'Username already exists','employees': employees, 'socials': socials, 'designations': designations})

            if Employee.objects.filter(email=email).exists():
                return render(request, 'hrms/employee.html', {'error': 'An employee with this email already exists','employees': employees, 'socials': socials, 'designations': designations})

            if Employee.objects.filter(employee_id=employee_id).exists():
                return render(request, 'hrms/employee.html', {'error': 'An employee with this Employee ID already exists','employees': employees, 'socials': socials, 'designations': designations})

            # Create the User object
            user = User.objects.create_user(username=username, password=password, email=email)
            if is_admin:
                user.is_superuser = True
                user.is_staff = True
                user.save()
            # Create the Employee object
            employee = Employee.objects.create(
                user=user,  # Associate the User with the Employee
                first_name=first_name,
                last_name=last_name,
                contact_number=contact_number,
                email=email,
                employee_id=employee_id,
                address=address,
                designation=designation,
                joining_date=joining_date,
                employee_photo=employee_photo,
            )

            # Redirect to the employee list page or success page
            return redirect('employee_view')  # Redirect to employee list after successful creation

        return render(request, 'hrms/employee.html', {'employees': employees, 'socials': socials, 'designations': designations})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def employee_details_view(request, id):
    if request.user.is_staff or request.user.is_superuser:
        # Fetch the employee object or return a 404
        employee = get_object_or_404(Employee, id=id)
        
        attendance_sheet = MonthlyAttendance.objects.filter(employee=employee.user).order_by('year', 'month')
        designations = Designation.objects.all()

        # Check if additional info exists or create a new instance
        additional_info, _ = EmployeeAdditionalInfo.objects.get_or_create(employee=employee)

        # Check if emergency contact exists or create a new instance
        emergency_contact, _ = EmergencyContact.objects.get_or_create(user=employee.user)
        
        social_media, _ = EmployeeSocialMedia.objects.get_or_create(employee=employee)
        
        bank_details, _ = EmployeeBankDetails.objects.get_or_create(employee=employee)

        if request.method == 'POST':
            if 'submit_employee_details' in request.POST:
                # Handle Employee fields
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                contact_number = request.POST.get('contact_number')
                email = request.POST.get('email')
                joining_date = request.POST.get('joining_date')
                employee_photo = request.FILES.get('employee_photo')

                employee.first_name = first_name
                employee.last_name = last_name
                employee.contact_number = contact_number
                employee.email = email
                employee.joining_date = joining_date
                if employee_photo:
                    employee.employee_photo = employee_photo
                employee.save()

                # Update EmployeeAdditionalInfo fields
                date_of_birth = request.POST.get('date_of_birth')
                gender = request.POST.get('gender')
                department = request.POST.get('department')
                designation = request.POST.get('designation')

                additional_info.date_of_birth = date_of_birth
                additional_info.gender = gender
                additional_info.department = department
                additional_info.designation = designation
                additional_info.save()

                messages.success(request, 'Employee details updated successfully!')

            elif 'submit_emergency_contact' in request.POST:
                # Handle Emergency Contact fields
                primary_full_name = request.POST.get('primary_full_name')
                primary_relationship = request.POST.get('primary_relationship')
                primary_phone_1 = request.POST.get('primary_phone_1')
                primary_phone_2 = request.POST.get('primary_phone_2')
                primary_email = request.POST.get('primary_email')
                primary_address = request.POST.get('primary_address')

                secondary_full_name = request.POST.get('secondary_full_name')
                secondary_relationship = request.POST.get('secondary_relationship')
                secondary_phone_1 = request.POST.get('secondary_phone_1')
                secondary_phone_2 = request.POST.get('secondary_phone_2')
                secondary_email = request.POST.get('secondary_email')
                secondary_address = request.POST.get('secondary_address')

                # Update EmergencyContact fields
                emergency_contact.primary_full_name = primary_full_name
                emergency_contact.primary_relationship = primary_relationship
                emergency_contact.primary_phone_1 = primary_phone_1
                emergency_contact.primary_phone_2 = primary_phone_2
                emergency_contact.primary_email = primary_email
                emergency_contact.primary_address = primary_address

                emergency_contact.secondary_full_name = secondary_full_name
                emergency_contact.secondary_relationship = secondary_relationship
                emergency_contact.secondary_phone_1 = secondary_phone_1
                emergency_contact.secondary_phone_2 = secondary_phone_2
                emergency_contact.secondary_email = secondary_email
                emergency_contact.secondary_address = secondary_address
                emergency_contact.save()

                messages.success(request, 'Emergency contact details updated successfully!')
                
            elif 'submit_social_media' in request.POST:
                # Handle Social Media details form submission
                instagram = request.POST.get('instagram')
                facebook = request.POST.get('facebook')
                linkedin = request.POST.get('linkedin')
                twitter = request.POST.get('twitter')
                whatsapp = request.POST.get('whatsapp')

                social_media.instagram = instagram
                social_media.facebook = facebook
                social_media.linkedin = linkedin
                social_media.twitter = twitter
                social_media.whatsapp = whatsapp
                social_media.save()
                
                messages.success(request, 'Social Media details updated successfully!')
                
            elif 'submit_bank_account' in request.POST:
                # Handle form submission for bank details
                account_holder_name = request.POST.get('account_holder_name')
                bank_name = request.POST.get('bank_name')
                account_number = request.POST.get('account_number')
                confirm_account_number = request.POST.get('confirm_account_number')
                branch_name = request.POST.get('branch_name')
                ifsc_code = request.POST.get('ifsc_code')

                # Ensure account number and confirm account number match
                if account_number != confirm_account_number:
                    messages.error(request, "Account numbers do not match!")
                    return redirect('employee-bank-details', id=employee.id)  # Redirect back to the same page

                # Update or create bank details for the employee
                bank_details.account_holder_name = account_holder_name
                bank_details.bank_name = bank_name
                bank_details.account_number = account_number
                bank_details.confirm_account_number = confirm_account_number
                bank_details.branch_name = branch_name
                bank_details.ifsc_code = ifsc_code
                bank_details.save()

                messages.success(request, 'Bank details updated successfully!')
                
                

            return redirect('employee-details', id=employee.id)  # Adjust 'employee-details' to your URL name

        context = {
            'employee': employee,
            'additional_info': additional_info,
            'emergency_contact': emergency_contact,
            'social_media': social_media,
            'bank_details': bank_details,
            'attendance_sheet' : attendance_sheet,
            'designations' : designations
        }
        return render(request, 'hrms/employee-details.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
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
        return render(request,'hrms/candidate-profile.html',{'candidate':candidate})
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
        return render (request,'hrms/candidate-registration.html',context)    
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
        return render (request,'hrms/candidate-list.html',{'candidates':candidates,'districts':districts})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
def designation_view(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('name')
            department = request.POST.get('department')
            designation = Designation.objects.create(name=name, department=department)
            messages.success(request, 'Designation created successfully!')

            return redirect('designation_view') 
        designations = Designation.objects.all()

        context = {
            'designations': designations
        }
        return render(request, 'hrms/designation.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
def delete_designation(request, id):
    # Get the designation object or return a 404 if not found
    designation = get_object_or_404(Designation, id=id)
    
    # Delete the designation
    designation.delete()
    messages.success(request, 'Designation deleted successfully!')

    return redirect('designation_view')
def attendence_view(request):
    if request.user.is_staff or request.user.is_superuser:
        # Fetch all employees from Employee model (which is related to User)
        employees = Employee.objects.all()
        holidays = Holiday.objects.values_list('date', flat=True)
        
        # Create a dictionary to hold attendance data for each employee
        attendance_data = {}
        today = date.today()
        num_days = calendar.monthrange(today.year, today.month)[1]

        for employee in employees:
            attendance_data[employee.id] = {
                "employee": employee,
                "attendance": []
            }
            
            # Generate attendance for the current month
            for day in range(1, num_days + 1):
                current_date = date(today.year, today.month, day)
                
                # Default status
                status = 'present'
                
                # Check if the date is a holiday
                if current_date in holidays or current_date.weekday() == 6:  # 6 represents Sunday
                    status = 'holiday'
                # Check if the employee is on leave
                elif LeaveRequest.objects.filter(
                    employee=employee,  # Corrected here
                    start_date__lte=current_date, 
                    end_date__gte=current_date, 
                    status='Approved'
                ).exists():
                    status = 'on_leave'
                
                # Add to attendance
                attendance_data[employee.id]["attendance"].append({
                    "date": current_date,
                    "status": status
                })

        return render(request, 'hrms/attendence.html', {'attendance_data': attendance_data, 'days_range': range(1, num_days + 1)})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)




def save_monthly_attendance():
    if request.user.is_staff or request.user.is_superuser:
        today = date.today()
        year = today.year
        month = today.month
        first_day, last_day = monthrange(year, month)

        # Loop through all employees
        for user in User.objects.all():
            # Aggregate attendance data for the current month
            attendance_summary = Attendance.objects.filter(
                user=user,
                date__year=year,
                date__month=month
            ).values('status').annotate(count=Count('status'))

            # Prepare summary data
            summary = {'Present': 0, 'Absent': 0, 'Half Day': 0}
            for record in attendance_summary:
                summary[record['status']] = record['count']

            # Save data to MonthlyAttendance
            MonthlyAttendance.objects.update_or_create(
                employee=user,
                year=year,
                month=month,
                defaults={
                    'total_present': summary['Present'],
                    'total_absent': summary['Absent'],
                    'total_half_day': summary['Half Day'],
                },
            )
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

@login_required
def leave_request_view(request):
    if request.user.is_staff or request.user.is_superuser:
        leave_requests = LeaveRequest.objects.all().order_by('-id')
        return render(request, 'hrms/leave-request.html', {'leave_requests': leave_requests})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
@login_required
def update_leave_status(request, leave_id):
    if request.method == "POST":
        status = request.POST.get('status')
        leave_request = get_object_or_404(LeaveRequest, id=leave_id)

        # Update the status
        leave_request.status = status
        leave_request.save()

        return redirect('leave_request_view')


def holiday_view(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == "POST":
            # Adding a new holiday
            date = request.POST.get('date')
            day = request.POST.get('day')
            name = request.POST.get('name')
            if date and day and name:
                Holiday.objects.create(date=date, day=day, name=name)
            return redirect('holiday_view')  # Redirect to avoid form resubmission

        elif request.method == "GET" and "delete_id" in request.GET:
            # Deleting a holiday
            delete_id = request.GET.get("delete_id")
            holiday = get_object_or_404(Holiday, id=delete_id)
            holiday.delete()
            return redirect('holiday_view')  # Redirect to refresh the list after deletion

        # Fetch all holidays to display
        holidays = Holiday.objects.all().order_by('-id')
        return render(request, 'hrms/holiday.html', {'holidays': holidays})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)


def project_view(request) :
    if request.user.is_staff or request.user.is_superuser:
        return render(request,'hrms/projects.html')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)


def pay_list_view(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == 'GET' and 'employee' in request.GET:
            # Retrieve form values
            employee_id = request.GET.get('employee')
            basic_salary = float(request.GET.get('basic_salary', 0))
            dearness_allowance = float(request.GET.get('dearness_allowance', 0))
            transport_allowance = float(request.GET.get('transport_allowance', 0))
            mobile_allowance = float(request.GET.get('mobile_allowance', 0))
            bonus = float(request.GET.get('bonus', 0))
            others_earning = float(request.GET.get('others_earning', 0))
            provident_fund = float(request.GET.get('provident_fund', 0))
            security_deposit = float(request.GET.get('security_deposit', 0))
            personal_loan = float(request.GET.get('personal_loan', 0))
            early_leaving = float(request.GET.get('early_leaving', 0))

            # Assuming the employee_type should be a string value like "Full-time" or "Part-time"
            employee_type = request.GET.get('employee_type', 'Full-time')  # Default to 'Full-time'

            # Fetch the Employee object corresponding to the employee ID
            employee = Employee.objects.get(id=employee_id)

            # Create the Salary object with the provided data
            Salary.objects.create(
                employee=employee,  # Assign the Employee instance here
                basic_salary=basic_salary,
                dearness_allowance=dearness_allowance,
                transport_allowance=transport_allowance,
                mobile_allowance=mobile_allowance,
                bonus=bonus,
                others_earning=others_earning,
                provident_fund=provident_fund,
                security_deposit=security_deposit,
                personal_loan=personal_loan,
                early_leaving=early_leaving,
                employee_type=employee_type  # Ensure employee_type is passed
            )

            return redirect('pay_list_view')  # Redirect to the pay list page after saving

        # Display all salaries
        salaries = Salary.objects.select_related('employee')
        employees = Employee.objects.all()
        return render(request, 'hrms/paylist.html', {'salaries': salaries, 'employees': employees})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)



    
@login_required
def update_salary_status(request, salary_id):
    if request.method == "POST":
        status = request.POST.get('status')
        salary = get_object_or_404(Salary, id=salary_id)

        # Update the paid status
        salary.status = status
        salary.save()

        return redirect('pay_list_view')  # Replace with the appropriate view name


def delete_salary(request, id):
    # Fetch the salary record by ID
    salary = get_object_or_404(Salary, id=id)
    
    
    # Delete the salary record
    salary.delete()

    # Redirect to the pay list view or another appropriate view
    return redirect('pay_list_view')

def pay_slip_view(request, salary_id):
    if request.user.is_staff or request.user.is_superuser:
        salary = Salary.objects.get(id=salary_id)
        
        # Fetch employee details
        employee = salary.employee  # Assuming Salary has a foreign key to the Employee model
        bank_details = employee.bank_details

        # Calculate earnings and deductions
        total_earnings = (
            salary.basic_salary +
            salary.dearness_allowance +
            salary.transport_allowance +
            salary.mobile_allowance +
            salary.bonus +
            salary.others_earning
        )

        total_deductions = (
            salary.provident_fund +
            salary.security_deposit +
            salary.personal_loan +
            salary.early_leaving
        )

        net_pay = total_earnings - total_deductions
        net_pay_in_words = convert_number_to_words(net_pay)

        # Pass employee details along with salary details to the template
        context = {
            "bank_details" : bank_details,
            'salary': salary,
            'employee': employee,  # Pass employee details
            'total_earnings': total_earnings,
            'total_deductions': total_deductions,
            'net_pay': net_pay,
            'net_pay_in_words': net_pay_in_words,
            'company_name': 'EMTA INFOTECH',
        }

        return render(request, 'hrms/salary-slip.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def office_expense_view(request):
    if request.user.is_staff or request.user.is_superuser:
        employees = Employee.objects.all()
        office_expenses = OfficeExpense.objects.all().order_by('-id')

        # Get current month and year
        today = date.today()
        current_month = today.month
        current_year = today.year

        # Filter expenses for the current month
        monthly_expenses = office_expenses.filter(
            purchase_date__month=current_month, purchase_date__year=current_year
        )

        # Calculate totals
        total_paid = monthly_expenses.filter(paid_status='Paid').aggregate(total=Sum('amount'))['total'] or 0
        total_unpaid = monthly_expenses.filter(paid_status='Unpaid').aggregate(total=Sum('amount'))['total'] or 0
        total_partially_paid = monthly_expenses.filter(paid_status='Hold').aggregate(total=Sum('amount'))['total'] or 0
        total_expense_month = monthly_expenses.aggregate(total=Sum('amount'))['total'] or 0

        # Store total expense in MonthlyExpense model
        month_start = date(current_year, current_month, 1)
        monthly_expense_record, created = MonthlyExpense.objects.get_or_create(month=month_start, defaults={'total_expense': 0})
        monthly_expense_record.total_expense = total_expense_month
        monthly_expense_record.save()

        if request.method == 'POST':
            if 'update_paid_status' in request.POST:
                # Handle the status update request
                expense_id = request.POST.get('expense_id')
                new_status = request.POST.get('new_status')

                # Update the paid status in the database
                try:
                    expense = OfficeExpense.objects.get(id=expense_id)
                    expense.paid_status = new_status
                    expense.save()
                    return JsonResponse({'success': True, 'message': 'Status updated successfully'})
                except OfficeExpense.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Expense not found'})

            # Handle new expense creation
            employee_name = request.POST.get('employee_name')
            item_name = request.POST.get('item_name')
            purchase_date = request.POST.get('purchase_date')
            amount = request.POST.get('amount')
            paid_status = request.POST.get('paid_status','Unpaid')
            attech = request.FILES.get('attech')

            # Save to database
            OfficeExpense.objects.create(
                employee_name=employee_name,
                item_name=item_name,
                purchase_date=purchase_date,
                amount=amount,
                paid_status=paid_status,
                attech = attech
            )

            return redirect('office_expense_view')

        context = {
            'employees': employees,
            'OfficeExpenses': office_expenses,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
            'total_partially_paid': total_partially_paid,
            'total_expense_month': total_expense_month,
        }
        return render(request, 'hrms/office-expense.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def delete_expense(request, id):
    officeExpense = get_object_or_404(OfficeExpense, id=id)
    officeExpense.delete()
    return redirect('office_expense_view')


@login_required
def update_expense_status(request, expense_id):
    if request.method == "POST":
        paid_status = request.POST.get('paid_status')
        expense = get_object_or_404(OfficeExpense, id=expense_id)

        # Update the paid status
        expense.paid_status = paid_status
        expense.save()

        return redirect('office_expense_view')  # Replace with the appropriate view name


def incentive_view(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            # Get the form data from the POST request
            employee_name_id = request.POST.get('employee_name')
            amount = request.POST.get('amount')
            reason = request.POST.get('reason')

            # Create and save the new incentive record
            try:
                employee = Employee.objects.get(id=employee_name_id)  # Assuming you're using Django's User model for employees
                incentive = Incentive(employee_name=employee, amount=amount, reason=reason)
                incentive.save()
                return redirect('incentive_view')  # Redirect to the same page or a success page
            except Employee.DoesNotExist:
                # Handle case where the employee does not exist
                return render(request, 'hrms/incentive.html', {'error': 'Employee not found'})

        # Handle GET request: Render the form
        employees = Employee.objects.all()  # Get all employees (assuming using Django's User model)
        current_month = timezone.now().month
        current_year = timezone.now().year

        incentives = Incentive.objects.filter(created_at__month=current_month, created_at__year=current_year).order_by('-id')
        
        # Calculate totals for different statuses
        total_incentive = incentives.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        total_paid = incentives.filter(status='Paid').aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        total_unpaid = incentives.filter(status='Unpaid').aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        total_hold = incentives.filter(status='Hold').aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        return render(request, 'hrms/incentive.html', {
            'employees' : employees,
            'incentives': incentives,
            'total_incentive': total_incentive,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
            'total_hold': total_hold
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def update_incentive_status(request, incentive_id):
    if request.method == 'POST':
        incentive = Incentive.objects.get(id=incentive_id)
        paid_status = request.POST.get('paid_status')
        incentive.status = paid_status
        incentive.save()
        return redirect('incentive_view')

def delete_incentive(request, incentive_id):
    incentive = get_object_or_404(Incentive, id=incentive_id)
    incentive.delete()
    return redirect('incentive_view') 

def bonus_view(request):
    if request.user.is_staff or request.user.is_superuser:
        employees = Employee.objects.all()  # Get all employees to populate the dropdown

        # Calculate total bonus, paid, unpaid, and hold amounts
        total_bonus = Bonus.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_paid = Bonus.objects.filter(status='Paid').aggregate(total=Sum('amount'))['total'] or 0
        total_unpaid = Bonus.objects.filter(status='Unpaid').aggregate(total=Sum('amount'))['total'] or 0
        total_hold = Bonus.objects.filter(status='Hold').aggregate(total=Sum('amount'))['total'] or 0

        if request.method == 'POST':
            # Extract data from the POST request
            employee_id = request.POST.get('employee')
            amount = request.POST.get('amount')
            reason = request.POST.get('reason')
            

            # Check if the data is valid
            if employee_id and amount and reason:
                try:
                    # Get the employee by ID
                    employee = Employee.objects.get(id=employee_id)

                    # Create a new bonus record
                    bonus = Bonus(employee=employee, amount=amount, reason=reason)
                    bonus.save()

                    messages.success(request, 'Bonus added successfully!')
                    return redirect('bonus_view')  # Redirect back to the bonus view

                except Employee.DoesNotExist:
                    messages.error(request, 'Employee not found.')
                except Exception as e:
                    messages.error(request, f'Error: {str(e)}')
            else:
                messages.error(request, 'All fields are required.')

        # Fetch all bonuses to display
        bonuses = Bonus.objects.all().order_by('-id')

        return render(request, 'hrms/bonus.html', {
            'bonuses': bonuses,
            'employees': employees,  # Pass employees to template
            'total_bonus': total_bonus,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
            'total_hold': total_hold,
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
def update_bonus_status(request, bonus_id):
    bonus = get_object_or_404(Bonus, id=bonus_id)

    if request.method == 'POST':
        status = request.POST.get('paid_status')

        if status in ['Paid', 'Unpaid', 'Hold']:
            bonus.status = status
            bonus.save()
            messages.success(request, f'Bonus status updated to {status}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('bonus_view')  # Redirect back to the bonus view
    
    
def delete_bonus(request, bonus_id):
    bonus = get_object_or_404(Bonus, id=bonus_id)
    bonus.delete()
    return redirect('bonus_view')

def resignation_view(request) :
    if request.user.is_staff or request.user.is_superuser:
        resignations = Resignation.objects.all()
        return render(request,'hrms/resignation.html',{'resignations':resignations})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def documents_view(request) :
    return render(request,'hrms/documents.html')

def promotion_view(request):
    if request.user.is_staff or request.user.is_superuser:
        employees = Employee.objects.all()
        designations = Designation.objects.all()
        promotions = Promotion.objects.all().order_by('-id')

        if request.method == "POST":
            employee_id = request.POST.get('employee')
            new_designation_id = request.POST.get('new_designation')
            promotion_title = request.POST.get('promotion_title')
            promotion_date = request.POST.get('promotion_date')
            description = request.POST.get('description')

            employee = Employee.objects.get(id=employee_id)
            new_designation = Designation.objects.get(id=new_designation_id)

            # Create a promotion record
            Promotion.objects.create(
                employee=employee,
                old_designation=employee.designation,
                new_designation=new_designation.name,
                promotion_date=promotion_date,
                description=description
            )

            Notification.objects.create(
                user=employee.user,  # Assuming `Employee` has a related `User` model
                notification_type='Promotion',
                message=f"You're Promoted {employee.designation} to {new_designation} on {promotion_date} . For : {description}.",
            )
            
            # Update the employee's designation if the promotion date is today or earlier
            if promotion_date <= timezone.now().date().isoformat():
                employee.designation = new_designation.name
                employee.save()
            else:
                # For future promotions, schedule the update using Celery or another task scheduler
                pass

            return redirect('promotion_view')

        return render(request, 'hrms/promotion.html', {'employees': employees, 'designations': designations, 'promotions' : promotions})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)



@shared_task
def update_designations():
    today = timezone.now().date()
    promotions = Promotion.objects.filter(promotion_date=today)

    for promotion in promotions:
        promotion.employee.current_designation = promotion.new_designation
        promotion.employee.save()

def delete_promotion(request, promotion_id):
    promotion = get_object_or_404(Promotion, id=promotion_id)
    promotion.delete()
    return redirect('promotion_view')



def termination_view(request):
    if request.user.is_staff or request.user.is_superuser:
        employees = Employee.objects.all()
        terminations = Termination.objects.all()
        notifications = Notification.objects.all()

        if request.method == "POST":
            employee_id = request.POST.get('employee')
            termination_type = request.POST.get('termination_type')
            notice_date = request.POST.get('notice_date')
            termination_date = request.POST.get('termination_date')
            description = request.POST.get('description')

            employee = Employee.objects.get(id=employee_id)

            # Create a Termination record
            Termination.objects.create(
                employee=employee,
                termination_type=termination_type,
                notice_date=notice_date,
                termination_date=termination_date,
                description=description
            )

            # Create a notification for the employee about the termination
            Notification.objects.create(
                user=employee.user,  # Assuming `Employee` has a related `User` model
                notification_type='termination',
                message=f'Your employment has been terminated. Termination type: {termination_type}.',
            )

            return redirect('termination_view')

        return render(request, 'hrms/termination.html', {'employees': employees, 'terminations': terminations,'notifications' : notifications})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)


def delete_termination(request, termination_id):
    termination = get_object_or_404(Termination, id=termination_id)
    termination.delete()
    return redirect('termination_view')

def announcement_view(request):
    if request.user.is_staff or request.user.is_superuser:
        announcements = Announcement.objects.all()
        if request.method == "POST":
            title = request.POST.get('title')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            description = request.POST.get('description')

            # Create a new Announcement record
            Announcement.objects.create(
                title=title,
                start_date=start_date,
                end_date=end_date,
                description=description
            )

            return redirect('announcement_view')  

        return render(request, 'hrms/Announcements.html',{'announcements': announcements})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    return redirect('announcement_view')

def team_meeting_view(request) :
    if request.user.is_staff or request.user.is_superuser:
        meetings = Meeting.objects.all()
        if request.method == 'POST':
            # Extract data from the POST request
            title = request.POST.get('title')
            date = request.POST.get('date')
            time = request.POST.get('time')
            department = request.POST.get('department')
            location = request.POST.get('location')

            # Validate the data
            if title and date and time and location:
                # Save the meeting data to the database
                meeting = Meeting(
                    title=title,
                    date=datetime.strptime(date, '%Y-%m-%d').date(),  # Convert string to date
                    time=datetime.strptime(time, '%H:%M').time(),# Convert string to time
                    department = department,
                    location=location
                )
                meeting.save()

                # Redirect to a success page or render a success message
                return redirect('team_meeting_view')
            else:
                # Return error if validation fails
                return HttpResponse('All fields are required!', status=400)
        else:
            return render(request,'hrms/team-meeting.html',{'meetings' : meetings})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
    
def delete_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    meeting.delete()
    return redirect('team_meeting_view')

def awards_view(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            # Get data from the form
            employee_id = request.POST.get('employee')
            award_type = request.POST.get('award_type')
            award_date = request.POST.get('award_date')
            gift = request.POST.get('gift')
            description = request.POST.get('description')

            # Validate data (simple example)
            if employee_id and award_type and award_date and gift and description:
                employee = Employee.objects.get(id=employee_id)

                # Create and save the new Award record
                Award.objects.create(
                    employee=employee,
                    award_type=award_type,
                    award_date=award_date,
                    gift=gift,
                    description=description
                )
                # Redirect to avoid form resubmission
                return redirect('awards_view')

        # Fetch all employees for the dropdown
        employees = Employee.objects.all()
        awards = Award.objects.all()
        return render(request, 'hrms/awards.html', {'employees': employees,'awards': awards})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def delete_award(request, award_id):
    award = get_object_or_404(Award, id=award_id)
    award.delete()
    return redirect('awards_view')

def office_activity_view(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == "POST":
            title = request.POST.get('title')
            activity_type = request.POST.get('activity_type')
            owner_name = request.POST.get('owner_name')
            start_date = request.POST.get('start_date')
            deadline = request.POST.get('deadline')

            # Create an OfficeActivity record
            OfficeActivity.objects.create(
                title=title,
                activity_type=activity_type,
                owner_name=owner_name,
                start_date=start_date,
                deadline=deadline
            )

            return redirect('office_activity_view')

        # Fetch all office activities to display
        activities = OfficeActivity.objects.all()
        return render(request, 'hrms/office-activity.html', {'activities': activities})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)

def delete_activity(request, officeactivity_id):
    activity = get_object_or_404(OfficeActivity, id=officeactivity_id)
    activity.delete()
    return redirect('office_activity_view')

def clients_view(request) :
    return render(request,'hrms/clients.html')

def warning_view(request):
    if request.user.is_staff or request.user.is_superuser:
        employees = Employee.objects.all()

        if request.method == "POST":
            employee_id = request.POST.get('employee')
            subject = request.POST.get('subject')
            warning_date = request.POST.get('warning_date')
            description = request.POST.get('description')

            # Convert warning_date to the correct format
            try:
                formatted_warning_date = datetime.strptime(warning_date, "%Y-%m-%d").date()
            except ValueError:
                formatted_warning_date = None

            # Get the employee instance
            employee = Employee.objects.get(id=employee_id)

            # Create a Warning record
            Warning.objects.create(
                employee=employee,
                subject=subject,
                warning_date=formatted_warning_date,
                description=description
            )
            Notification.objects.create(
            user=employee.user, 
            notification_type='Warning',
            message=f"{subject} on {warning_date} . For : {description}.",
            )

            return redirect('warning_view')

        # Fetch all warnings to display
        warnings = Warning.objects.all()
        return render(request, 'hrms/warning.html', {'employees': employees, 'warnings': warnings})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, '404.html', status=404)
        
def delete_warning(request, warning_id):
    warning = get_object_or_404(Warning, id=warning_id)
    warning.delete()
    return redirect('warning_view')

@login_required
def update_resignation_status(request, resignation_id):
    if request.method == "POST":
        status = request.POST.get('status')
        resignation = get_object_or_404(Resignation, id=resignation_id)

        # Update the status
        resignation.status = status
        resignation.save()

        return redirect('resignation_view')
    
@login_required
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
    return render(request, 'hrms/company-registration.html',{
        'districts' : districts,
        'job_sectors' : job_sectors,
        'departments' : departments
        })

def admin_company_list(request) :
    companys = Company_registration.objects.all().order_by('-id')
    return render(request,'hrms/company-list.html',{'companys':companys})

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
    return render(request,'hrms/company-profile.html',{'company':company})


def admin_vendor_list(request) :
    vendors = Vendor.objects.all().order_by('-id')
    return render(request,'hrms/admin-vendor-list.html',{'vendors':vendors})

def admin_evms_candidate_list(request) :
    candidates = Candidate.objects.all().order_by('-id')
    return render(request,'hrms/admin-evms-candidate-list.html',{'candidates':candidates})

# def admin_vendor_candidate_list(request,id) :
#     vendor = get_object_or_404(Vendor, id=id)
    
#     return render(request,'hrms/admin-vendor-candidate-list.html',{'candidates':candidates,'vendor':vendor})

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
    return render(request, 'hrms/admin-vendor-candidate-list.html', context)




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
    return render(request,'hrms/evms-candidate-profile.html ',context)

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
    return render(request,'hrms/evms-vendor-candidate-profile.html',context)