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
from App.models import *

def employee_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Create a new session record
            EmployeeSession.objects.create(user=user)
            return redirect('employee_dashboard')
        else:
            return render(request, 'employee/login.html', {'error': 'Invalid credentials'})
    return render(request, 'employee/login.html')

@login_required
def employee_logout(request):
    # Get the last session and set the logout time
    session = EmployeeSession.objects.filter(user=request.user, logout_time__isnull=True).last()
    if session:
        session.logout_time = now()
        session.save()
    logout(request)
    return redirect('employee_login')


@login_required
def employee_dashboard(request):
    if request.user.is_authenticated:
        today1 = date.today()
        today = datetime.today().date()
        start_of_month = today.replace(day=1)
        logged_in_employee = get_object_or_404(Employee, user=request.user)
        tasks = Task.objects.filter(assigned_to=logged_in_employee).order_by('-id')
        today = now().date()

        # Fetch all sessions for the logged-in user for today
        sessions = EmployeeSession.objects.filter(user=request.user, login_time__date=today).order_by('-id')

        # Compute total login time for today
        total_time = timedelta()
        session_data = []
        for session in sessions:
            # If logout_time is None, set duration to 0
            session_duration = session.total_time or timedelta()
            total_time += session_duration

            session_data.append({
                "login_time": session.login_time_ist.strftime('%Y-%m-%d %H:%M:%S'),
                "logout_time": (
                    session.logout_time_ist.strftime('%Y-%m-%d %H:%M:%S') if session.logout_time else "No Record"
                ),
                "total_time": str(session.total_time) if session.total_time else "N/A",
            })

        # Convert total login time to hours, minutes, and seconds
        hours, remainder = divmod(total_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        total_login_time_formatted = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        meetings = Meeting.objects.filter(date=today).order_by('-id')
        office_expenses = OfficeExpense.objects.filter(employee_name=logged_in_employee, purchase_date=today).order_by('-id')
        notifications = Notification.objects.filter(user=request.user).order_by('-id')
        selected_candidates = Candidate_registration.objects.filter(
            selection_status__in=['Selected', 'Pending', 'Rejected'],
            register_time__date=today1,
            employee_name=logged_in_employee
        ).order_by('-id')
        total_call_count = Candidate_registration.objects.filter(
            register_time__date=today1, employee_name=logged_in_employee
        ).count()
        total_connected_call = Candidate_registration.objects.filter(
            call_connection='Yes', register_time__date=today1, employee_name=logged_in_employee
        ).count()
        total_lead_generate = Candidate_registration.objects.filter(
            lead_generate='Yes', register_time__date=today1, employee_name=logged_in_employee
        ).count()
        total_placement = Candidate_registration.objects.filter(
            selection_status='Selected', register_time__date=today1, employee_name=logged_in_employee
        ).count()
        todays_earning = Candidate_registration.objects.filter(
            register_time__date=today1, employee_name=logged_in_employee
        ).aggregate(total_earning=Sum('emta_commission', output_field=models.FloatField()))['total_earning'] or 0.0
        monthly_earning = Candidate_registration.objects.filter(
            register_time__date__gte=start_of_month,
            register_time__date__lte=today,
            employee_name=logged_in_employee
        ).aggregate(total_earning=Sum('emta_commission', output_field=models.FloatField()))['total_earning'] or 0.0

        context = {
            'sessions': sessions,
            'meetings': meetings,
            'office_expenses': office_expenses,
            'notifications': notifications,
            'logged_in_employee': logged_in_employee,
            'tasks': tasks,
            'selected_candidates': selected_candidates,
            'total_call_count': total_call_count,
            'total_connected_call': total_connected_call,
            'total_lead_generate': total_lead_generate,
            'total_placement': total_placement,
            'todays_earning': todays_earning,
            'monthly_earning': monthly_earning,
            "sessions_json": json.dumps(session_data, indent=4),
            "total_login_time": total_login_time_formatted,
        }

        return render(request, 'employee/dashboard.html', context)
    else:
        return render(request, 'employee/login.html', {'error': 'User not authenticated'})


@login_required
def employee_profile_view(request,id):
    if request.user.is_authenticated:
        employee = get_object_or_404(Employee, user=request.user)
        
        # Check if additional info exists or create a new instance
        additional_info, _ = EmployeeAdditionalInfo.objects.get_or_create(employee=employee)

        # Check if emergency contact exists or create a new instance
        emergency_contact, _ = EmergencyContact.objects.get_or_create(user=employee.user)
        
        social_media, _ = EmployeeSocialMedia.objects.get_or_create(employee=employee)
        
        bank_details, _ = EmployeeBankDetails.objects.get_or_create(employee=employee)

        if request.method == 'POST':
            if 'employee_submit_employee_details' in request.POST:
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

            elif 'employee_submit_emergency_contact' in request.POST:
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
                
            elif 'employee_submit_social_media' in request.POST:
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
                
            elif 'employee_submit_bank_account' in request.POST:
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
                
                

            return redirect('employee_profile_view', id=employee.id)  # Adjust 'employee-details' to your URL name

        context = {
            'employee': employee,
            'additional_info': additional_info,
            'emergency_contact': emergency_contact,
            'social_media': social_media,
            'bank_details': bank_details,
        }
        return render(request, 'employee/profile.html', context)
    else:
        return render(request, 'employee/login.html', {'error': 'User not authenticated'})

@login_required
def employee_leave_request_view(request):
    logged_in_employee = Employee.objects.get(user=request.user)
    leave_requests = LeaveRequest.objects.filter(employee=logged_in_employee).order_by('-id')
    if request.method == "POST":
        reason = request.POST.get('name')  # Get the reason
        start_date = request.POST.get('start_date')  # Get the start date
        end_date = request.POST.get('end_date')  # Get the end date
        attachment = request.FILES.get('name')  # Get the file (if any)

        # Basic validation (you can expand this as needed)
        if not reason or not start_date or not end_date:
            return render(request, 'employee/leave-request.html', {
                'error': 'All fields are required!'
            })

        # Save the file if an attachment is uploaded
        if attachment:
            fs = FileSystemStorage()
            file_path = fs.save(attachment.name, attachment)
        else:
            file_path = None

        # Save the leave request to the database
        LeaveRequest.objects.create(
            employee=logged_in_employee,
            reason=reason,
            attachment=file_path,
            start_date=start_date,
            end_date=end_date
        )

        return redirect('employee_leave_request_view')  # Redirect to the leave request list view

    return render(request, 'employee/leave-request.html', {'leave_requests': leave_requests})


def employee_holiday_view(request):
    

    # Fetch all holidays to display
    holidays = Holiday.objects.all()
    return render(request, 'employee/holiday.html', {'holidays': holidays})



@login_required
def office_employee_expense_view(request):
    # Get the logged-in user and corresponding employee record
    logged_in_employee = Employee.objects.get(user=request.user)

    # Filter expenses specific to the logged-in employee
    office_expenses = OfficeExpense.objects.filter(employee_name=logged_in_employee).order_by('-id')

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
    monthly_expense_record, created = MonthlyExpense.objects.get_or_create(
        month=month_start, defaults={'total_expense': 0}
    )
    monthly_expense_record.total_expense = total_expense_month
    monthly_expense_record.save()

    if request.method == 'POST':
        # Handle new expense creation
        item_name = request.POST.get('item_name')
        purchase_date = request.POST.get('purchase_date')
        amount = request.POST.get('amount')
        paid_status = request.POST.get('paid_status', 'Unpaid')
        attech = request.FILES.get('attech')

        # Save to database
        OfficeExpense.objects.create(
            employee_name=logged_in_employee,
            item_name=item_name,
            purchase_date=purchase_date,
            amount=amount,
            paid_status=paid_status,
            attech = attech
        )

        return redirect('office_employee_expense_view')

    context = {
        'logged_in_employee': logged_in_employee,
        'OfficeExpenses': office_expenses,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'total_partially_paid': total_partially_paid,
        'total_expense_month': total_expense_month,
    }
    return render(request, 'employee/employee-expense.html', context)


def base_view(request) :
    employees = Employee.objects.all()
    return render(request,'employee/base.html',{"employees" : employees})



@login_required
def employee_resignation_view(request):
    logged_in_employee = Employee.objects.get(user=request.user)
    resignations = Resignation.objects.filter(employee=logged_in_employee)
    if request.method == 'POST':
        status = request.POST.get('status','Pending')
        resignation_date = request.POST.get('resignation_date')
        last_working_day = request.POST.get('last_working_day')
        description = request.POST.get('description')
        
        # Parse the resignation date to a datetime object
        resignation_date = dateparse.parse_date(resignation_date)
        
        # Save the resignation details to the database
        Resignation.objects.create(
            employee=logged_in_employee,
            status=status,
            resignation_date=resignation_date,
            last_working_day=last_working_day,
            description=description
        )
        
        return redirect('employee_resignation_view')  # Redirect to a success page

    context = {
        'logged_in_employee': logged_in_employee,
        'resignations': resignations
    }
    return render(request, 'employee/resignation.html',context)

def delete_employee_resignation_view(request, resignation_id):
    resignation = get_object_or_404(Resignation, id=resignation_id)
    resignation.delete()
    return redirect('employee_resignation_view') 

def assign_task(request) :
    employees = Employee.objects.all()
    tasks = Task.objects.all().order_by('-id')
    if request.method == 'POST':
        # Extract data from the POST request
        
        title = request.POST.get('title')
        description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority')

        # Validate the data
        if not title or not description or not assigned_to_id or not due_date or not priority:
            return render(request, 'hrms/assign-task.html', {
                'error': 'All fields are required!'
            })

        # Save the task to the database
        assigned_to = Employee.objects.get(id=assigned_to_id)
        Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            due_date=due_date,
            priority=priority
        )

        return redirect('assign_task')  # Redirect to the task list view

    return render(request, 'hrms/assign-task.html', {'employees': employees, 'tasks': tasks})

def update_task_status(request,task_id) :
    if request.method == 'POST':
        task = get_object_or_404(Task,id=task_id)
        status = request.POST.get('status')
        task.status = status
        task.save()

        return redirect('employee_dashboard')  # Redirect to the task list view
    
def employee_update_task_status(request,task_id) :
    if request.method == 'POST':
        task = get_object_or_404(Task,id=task_id)
        status = request.POST.get('status')
        task.status = status
        task.save()

        return redirect('assign_task')

def employee_candidate_list(request) :
    logged_in_employee = Employee.objects.get(user=request.user)
    candidates = Candidate_registration.objects.filter(employee_name=logged_in_employee).order_by('-id')
    return render (request,'employee/candidate-list.html',{'candidates':candidates})
    
def employee_candidate_registration(request) :
    logged_in_employee = Employee.objects.get(user=request.user)
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
    
        return redirect('employee_candidate_list')
    
    suggested_unique_code = get_next_unique_code()
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
    return render (request,'employee/candidate-registration.html',context)    

def get_next_unique_code():
    candidate = Candidate_registration.objects.filter(unique_code__regex=r'^EC\d{6}$').values_list('unique_code', flat=True)
    numbers = [int(re.search(r'\d{6}', unique_code).group()) for unique_code in candidate]

    if numbers:
        next_number = max(numbers) + 1  
    else:
        next_number = 1 
    return f"EC{next_number:06d}"


def employee_candidate_profile(request,id) :
    logged_in_employee = Employee.objects.get(user=request.user)
    candidate = get_object_or_404(Candidate_registration, id=id, employee_name=logged_in_employee)

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
            
            

        return redirect('employee_candidate_profile', id=id)
    context = {
        'logged_in_employee': logged_in_employee,
        'candidate': candidate
    }
    return render(request,'employee/candidate-profile.html',context)


@login_required
def employee_company_registration(request):
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
        return redirect('employee_company_list')
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
    return render(request, 'employee/company-registration.html',{
        'districts' : districts,
        'job_sectors' : job_sectors,
        'departments' : departments
        })

def employee_company_list(request) :
    companys = Company_registration.objects.all().order_by('-id')
    return render(request,'employee/company-list.html',{'companys':companys})

def employee_company_profile(request,id) :
    company = get_object_or_404(Company_registration, id=id)
    if request.method == 'POST':
        if 'company_personal_information' in request.POST:
            # Handle Employee fields
            company_name = request.POST.get('company_name')
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
            company_email_address=company_email_address
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
        return redirect('employee_company_profile', id=id)
    return render(request,'employee/company-profile.html',{'company':company})