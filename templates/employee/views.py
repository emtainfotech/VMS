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
from EVMS.models import *
from django.core.paginator import Paginator
import uuid
from django.utils.dateparse import parse_datetime
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
import pandas as pd
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings


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
    if request.method == "POST":
        logout_reason = request.POST.get("logout_reason", "Employee is not working for 5 minutes")

        # Get the last session and set the logout time and reason
        session = EmployeeSession.objects.filter(user=request.user, logout_time__isnull=True).last()
        if session:
            session.logout_time = now()
            session.logout_reason = logout_reason  # Store the reason for logout
            session.save()

        # Perform the logout
        logout(request)

    return redirect('employee_login')  # Redirect to login page after logout

@login_required
def employee_dashboard(request):
    if request.user.is_authenticated:
        today1 = date.today()
        today = datetime.today().date()
        start_of_month = today.replace(day=1)
        logged_in_employee = get_object_or_404(Employee, user=request.user)
        additional_info, _ = EmployeeAdditionalInfo.objects.get_or_create(employee=logged_in_employee)
        tasks = Task.objects.filter(assigned_to=logged_in_employee).order_by('-id')
        today = now().date()

        # Fetch all sessions for today for the logged-in user
        sessions = EmployeeSession.objects.filter(user=request.user, punch_in_time__date=today)

        # Initialize session to None
        session = None

        # Calculate total login duration for today
        total_work_duration = timedelta()  # Initialize to 0 duration
        for session in sessions:
            if session.punch_out_time:
                # Add the duration of completed sessions
                total_work_duration += session.punch_out_time - session.punch_in_time
            else:
                # If the session is ongoing, calculate duration up to the current time
                total_work_duration += now() - session.punch_in_time

        # Convert the total duration to a readable format
        hours, remainder = divmod(total_work_duration.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        total_punch_in_time_formatted = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Get the first login of the day, if any
        first_punch_in_time = sessions.first().punch_in_time if sessions.exists() else None

        meetings = Meeting.objects.filter(date=today).order_by('-id')
        office_expenses = OfficeExpense.objects.filter(employee_name=logged_in_employee, purchase_date=today).order_by('-id')
        # notifications = Notification.objects.filter(user=request.user).order_by('-id')
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
            'session': session,
            'sessions': sessions,
            'meetings': meetings,
            'additional_info' : additional_info,
            'office_expenses': office_expenses,
            # 'notifications': notifications,
            'logged_in_employee': logged_in_employee,
            'tasks': tasks,
            'selected_candidates': selected_candidates,
            'total_call_count': total_call_count,
            'total_connected_call': total_connected_call,
            'total_lead_generate': total_lead_generate,
            'total_placement': total_placement,
            'todays_earning': todays_earning,
            'monthly_earning': monthly_earning,
            "total_punch_in_time_formatted": total_punch_in_time_formatted,
            'first_punch_in_time': first_punch_in_time
        }

        return render(request, 'employee/dashboard.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def punch_in(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # Check if the employee already has an open session for today
            today = now().date()
            open_session = EmployeeSession.objects.filter(user=request.user, punch_in_time__date=today, punch_out_time=None).first()

            if open_session:
                return JsonResponse({'error': 'Already punched in'}, status=400)

            # Create a new session record
            session = EmployeeSession.objects.create(user=request.user, punch_in_time=now())
            return JsonResponse({'message': 'Punch In successful', 'punch_in_time': session.punch_in_time.strftime('%Y-%m-%d %H:%M:%S')})

        return JsonResponse({'error': 'Invalid request'}, status=400)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def punch_out(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            punch_out_reason = request.POST.get('punch_out_reason', '')

            # Find the employee's open session
            today = now().date()
            open_session = EmployeeSession.objects.filter(user=request.user, punch_in_time__date=today, punch_out_time=None).first()

            if not open_session:
                return JsonResponse({'error': 'No open session to punch out'}, status=400)

            # Set the logout time and reason
            open_session.punch_out_time = now()
            open_session.total_time = open_session.punch_out_time - open_session.punch_in_time
            open_session.punch_out_reason = punch_out_reason
            open_session.save()

            return JsonResponse({'message': 'Punch Out successful', 'punch_out_time': open_session.punch_out_time.strftime('%Y-%m-%d %H:%M:%S')})

        return JsonResponse({'error': 'Invalid request'}, status=400)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_profile_view(request,id):
    if request.user.is_authenticated:
        # Fetch the employee object or return a 404
        employee = get_object_or_404(Employee, user=request.user)
        attendance_sheet = MonthlyAttendance.objects.filter(employee=employee.user).order_by('year', 'month')
        designations = Designation.objects.all()
        additional_info, _ = EmployeeAdditionalInfo.objects.get_or_create(employee=employee)
        address_details, _ = Employee_address.objects.get_or_create(employee=employee)
        bank_details, _ = EmployeeBankDetails.objects.get_or_create(employee=employee)

        if request.method == 'POST':
            if 'submit_employee_details' in request.POST:
                # Handle Employee fields
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                contact_number = request.POST.get('contact_number')
                email = request.POST.get('email')
                joining_date = request.POST.get('joining_date') or None
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
                date_of_birth = request.POST.get('date_of_birth') or None
                gender = request.POST.get('gender')
                department = request.POST.get('department')
                designation = request.POST.get('designation')
                blood_group = request.POST.get('blood_group')
                reporting_to = request.POST.get('reporting_to')

                additional_info.date_of_birth = date_of_birth
                additional_info.gender = gender
                employee.department = department
                employee.designation = designation
                additional_info.blood_group = blood_group
                additional_info.reporting_to = reporting_to
                additional_info.save()

                messages.success(request, 'Employee details updated successfully!')

            elif 'sumbit_family_details' in request.POST:
                # Handle Emergency Contact fields
                member_name = request.POST.get('member_name')
                relation = request.POST.get('relation')
                contact_number = request.POST.get('contact_number')
                date_of_birth = request.POST.get('date_of_birth') or None

                Family_details.objects.create(
                    employee=employee,
                    member_name=member_name,
                    relation=relation,
                    contact_number=contact_number,
                    date_of_birth=date_of_birth
                )

                messages.success(request, 'Emergency contact details updated successfully!')
                
            elif 'submit_address_details' in request.POST:
                # Handle Social Media details form submission
                permanent_address = request.POST.get('permanent_address')
                present_address = request.POST.get('present_address')
                city = request.POST.get('city')
                state = request.POST.get('state')
                country = request.POST.get('country')
                zip_code = request.POST.get('zip_code')
                nationality = request.POST.get('nationality')

                address_details.permanent_address = permanent_address
                address_details.present_address = present_address
                address_details.city = city
                address_details.state = state
                address_details.country = country
                address_details.zip_code = zip_code
                address_details.nationality = nationality
                address_details.save()
                
                messages.success(request, 'Address details updated successfully!')
                
            elif 'submit_education_details' in request.POST:
                # Retrieve form data
                cource_name = request.POST.get('cource_name')
                institution_name = request.POST.get('institution_name')
                start_year = request.POST.get('start_year') or None
                end_year = request.POST.get('end_year') or None
                grade = request.POST.get('grade')
                description = request.POST.get('description')
                education_certificate = request.FILES.get('education_certificate')

                # Create a new education record for the employee
                Education_details.objects.create(
                    employee=employee,  # Ensure you have the employee instance already fetched
                    cource_name=cource_name,
                    institution_name=institution_name,
                    start_year=start_year,
                    end_year=end_year,
                    grade=grade,
                    description=description,
                    education_certificate=education_certificate
                )

                # Add a success message
                messages.success(request, 'Education details updated successfully!')

            
            elif 'submit_experience_details' in request.POST:
                # Handle Social Media details form submission
                organization_name = request.POST.get('organization_name')
                designation_name = request.POST.get('designation_name')
                start_date = request.POST.get('start_date') or None
                end_date = request.POST.get('end_date') or None
                description = request.POST.get('description')
                experience_certificate = request.FILES.get('experience_certificate')

                Experience_details.objects.create(
                    employee = employee,
                    organization_name = organization_name,
                    designation_name = designation_name,
                    start_date = start_date,
                    end_date = end_date,
                    description = description,
                    experience_certificate = experience_certificate
                )
                
                messages.success(request, 'Experience details updated successfully!')
             
            elif 'submit_documents_details' in request.POST:
                document_number = request.POST.get('document_number')
                document_type = request.POST.get('document_type')
                document_file = request.FILES.get('document_file')

                # Create a new document record for the employee
                Documents_details.objects.create(
                    employee=employee,  # Use the employee fetched at the start of the view
                    document_type=document_type,
                    document_number=document_number,
                    document_file=document_file
                )

                messages.success(request, 'Document details added successfully!')

                
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
                
                

            return redirect('employee_profile_view', id=employee.id)  # Adjust 'employee-details' to your URL name
        # Get all document details related to the employee
        docs = Documents_details.objects.filter(employee=employee)
        education_details = Education_details.objects.filter(employee=employee)
        experience_details = Experience_details.objects.filter(employee=employee)
        family_details = Family_details.objects.filter(employee=employee)

        context = {
            'employee': employee,
            'additional_info': additional_info,
            'address_details': address_details,
            'family_details' : family_details,
            'education_details' : education_details,
            'experience_details' : experience_details,
            'bank_details': bank_details,
            'attendance_sheet' : attendance_sheet,
            'designations' : designations,
            'docs' : docs
        }
        return render(request, 'employee/employee-profile.html', context)
    else:
        return render(request, 'employee/login.html', {'error': 'User not authenticated'})

@login_required
def employee_leave_request_view(request):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        leave_requests = LeaveRequest.objects.filter(employee=logged_in_employee).order_by('-created_at')
        
        # Calculate days count for each leave request
        for leave in leave_requests:
            leave.days_count = (leave.end_date - leave.start_date).days + 1
        
        if request.method == "POST":
            reason = request.POST.get('reason')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            attachment = request.FILES.get('attachment')
            
            if not reason or not start_date or not end_date:
                return render(request, 'employee/leave-request.html', {
                    'error': 'All required fields must be filled!',
                    'leave_requests': leave_requests,
                    'today': date.today()
                })
            
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                
                if end_date < start_date:
                    return render(request, 'employee/leave-request.html', {
                        'error': 'End date must be after start date!',
                        'leave_requests': leave_requests,
                        'today': date.today()
                    })
                    
                LeaveRequest.objects.create(
                    employee=logged_in_employee,
                    reason=reason,
                    attachment=attachment,
                    start_date=start_date,
                    end_date=end_date,
                    status='Pending'
                )
                
                messages.success(request, 'Leave request submitted successfully!')
                return redirect('employee_leave_request_view')
                
            except ValueError:
                return render(request, 'employee/leave-request.html', {
                    'error': 'Invalid date format!',
                    'leave_requests': leave_requests,
                    'today': date.today()
                })
        
        return render(request, 'employee/leave-request.html', {
            'leave_requests': leave_requests,
            'today': date.today()
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def edit_leave_request(request, leave_id):
    if request.user.is_authenticated:
        try:
            leave_request = LeaveRequest.objects.get(id=leave_id, employee__user=request.user)
            
            if leave_request.status != 'Pending':
                messages.error(request, 'Only pending leave requests can be edited!')
                return redirect('employee_leave_request_view')
                
            if request.method == "POST":
                reason = request.POST.get('reason')
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')
                attachment = request.FILES.get('attachment')
                
                if not reason or not start_date or not end_date:
                    messages.error(request, 'All required fields must be filled!')
                    return redirect('employee_leave_request_view')
                
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    
                    if end_date < start_date:
                        messages.error(request, 'End date must be after start date!')
                        return redirect('employee_leave_request_view')
                        
                    leave_request.reason = reason
                    leave_request.start_date = start_date
                    leave_request.end_date = end_date
                    
                    if attachment:
                        if leave_request.attachment:
                            # Delete old attachment if it exists
                            leave_request.attachment.delete()
                        leave_request.attachment = attachment
                        
                    leave_request.save()
                    messages.success(request, 'Leave request updated successfully!')
                    return redirect('employee_leave_request_view')
                    
                except ValueError:
                    messages.error(request, 'Invalid date format!')
                    return redirect('employee_leave_request_view')
                    
            return redirect('employee_leave_request_view')
            
        except LeaveRequest.DoesNotExist:
            messages.error(request, 'Leave request not found!')
            return redirect('employee_leave_request_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def delete_leave_request(request, leave_id):
    if request.user.is_authenticated:
        try:
            leave_request = LeaveRequest.objects.get(id=leave_id, employee__user=request.user)
            
            if leave_request.status != 'Pending':
                messages.error(request, 'Only pending leave requests can be deleted!')
                return redirect('employee_leave_request_view')
                
            if request.method == "POST":
                if leave_request.attachment:
                    leave_request.attachment.delete()
                leave_request.delete()
                messages.success(request, 'Leave request deleted successfully!')
                
            return redirect('employee_leave_request_view')
            
        except LeaveRequest.DoesNotExist:
            messages.error(request, 'Leave request not found!')
            return redirect('employee_leave_request_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_holiday_view(request):
    if request.user.is_authenticated:

        # Fetch all holidays to display
        holidays = Holiday.objects.all()
        return render(request, 'employee/holiday.html', {'holidays': holidays})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def office_employee_expense_view(request):
    if request.user.is_authenticated:
        # Get the logged-in user and corresponding employee record
        logged_in_employee = Employee.objects.get(user=request.user)

        # Get all expenses for the logged-in employee
        office_expenses = OfficeExpense.objects.filter(employee_name=logged_in_employee).order_by('-purchase_date')

        # Pagination
        paginator = Paginator(office_expenses, 10)  # Show 10 expenses per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Get current month and year
        today = date.today()
        current_month = today.month
        current_year = today.year

        # Filter expenses for the current month
        monthly_expenses = office_expenses.filter(
            purchase_date__month=current_month, 
            purchase_date__year=current_year
        )

        # Calculate totals
        total_paid = monthly_expenses.filter(paid_status='Paid').aggregate(total=Sum('amount'))['total'] or 0
        total_unpaid = monthly_expenses.filter(paid_status='Unpaid').aggregate(total=Sum('amount'))['total'] or 0
        total_partially_paid = monthly_expenses.filter(paid_status='Hold').aggregate(total=Sum('amount'))['total'] or 0
        total_expense_month = monthly_expenses.aggregate(total=Sum('amount'))['total'] or 0

        # Store total expense in MonthlyExpense model
        month_start = date(current_year, current_month, 1)
        monthly_expense_record, created = MonthlyExpense.objects.get_or_create(
            month=month_start, 
            defaults={'total_expense': 0}
        )
        monthly_expense_record.total_expense = total_expense_month
        monthly_expense_record.save()

        if request.method == 'POST':
            # Check if this is an edit request
            if 'expense_id' in request.POST:
                return handle_edit_expense(request, logged_in_employee)
            # Check if this is a delete request
            elif 'delete_id' in request.POST:
                return handle_delete_expense(request)
            # Otherwise handle new expense creation
            else:
                return handle_new_expense(request, logged_in_employee)

        context = {
            'logged_in_employee': logged_in_employee,
            'OfficeExpenses': page_obj,
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
            'total_partially_paid': total_partially_paid,
            'total_expense_month': total_expense_month,
            'current_month': f"{current_year}-{current_month:02d}",
            'employee': logged_in_employee,
            'today': today.strftime('%Y-%m-%d')
        }
        return render(request, 'employee/employee-expense.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def handle_new_expense(request, logged_in_employee):
    if request.user.is_authenticated:
        """Handle creation of new expense"""
        item_name = request.POST.get('item_name')
        purchase_date = request.POST.get('purchase_date')
        amount = request.POST.get('amount')
        paid_status = request.POST.get('paid_status', 'Unpaid')
        description = request.POST.get('description', '')
        attech = request.FILES.get('attech')

        OfficeExpense.objects.create(
            employee_name=logged_in_employee,
            item_name=item_name,
            purchase_date=purchase_date,
            amount=amount,
            paid_status=paid_status,
            description=description,
            attech=attech
        )
        return redirect('office_employee_expense_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def handle_edit_expense(request, logged_in_employee):
    if request.user.is_authenticated:
        """Handle editing an existing expense"""
        expense_id = request.POST.get('expense_id')
        expense = get_object_or_404(OfficeExpense, id=expense_id, employee_name=logged_in_employee)
        
        expense.item_name = request.POST.get('item_name')
        expense.purchase_date = request.POST.get('purchase_date')
        expense.amount = request.POST.get('amount')
        expense.paid_status = request.POST.get('paid_status', 'Unpaid')
        expense.description = request.POST.get('description', '')
        
        # Only update attachment if a new file was provided
        if 'attech' in request.FILES:
            expense.attech = request.FILES.get('attech')
        
        expense.save()
        return redirect('office_employee_expense_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def handle_delete_expense(request):
    if request.user.is_authenticated:
        """Handle deleting an expense"""
        expense_id = request.POST.get('delete_id')
        expense = get_object_or_404(OfficeExpense, id=expense_id)
        expense.delete()
        return redirect('office_employee_expense_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

def base_view(request) :
    employees = Employee.objects.all()
    return render(request,'employee/base.html',{"employees" : employees})

@login_required
def employee_resignation_view(request):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        
        # Get all resignations for the logged-in employee
        resignations_list = Resignation.objects.filter(employee=logged_in_employee).order_by('-resignation_date')
        
        # Pagination
        paginator = Paginator(resignations_list, 10)  # Show 10 resignations per page
        page_number = request.GET.get('page')
        resignations = paginator.get_page(page_number)
        
        if request.method == 'POST':
            # Handle form submission
            resignation_date = request.POST.get('resignation_date')
            last_working_day = request.POST.get('last_working_day')
            description = request.POST.get('description')
            status = 'Pending'  # Default status
            
            # Create new resignation
            Resignation.objects.create(
                employee=logged_in_employee,
                resignation_date=resignation_date,
                last_working_day=last_working_day,
                description=description,
                status=status
            )
            
            return redirect('employee_resignation_view')

        context = {
            'logged_in_employee': logged_in_employee,
            'resignations': resignations
        }
        return render(request, 'employee/resignation.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def edit_employee_resignation_view(request, resignation_id):
    if request.user.is_authenticated:
        resignation = get_object_or_404(Resignation, id=resignation_id, employee__user=request.user)
        
        if request.method == 'POST':
            # Update resignation details
            resignation.resignation_date = request.POST.get('resignation_date')
            resignation.last_working_day = request.POST.get('last_working_day')
            resignation.description = request.POST.get('description')
            resignation.status = request.POST.get('status', 'Pending')
            resignation.save()
            
            return redirect('employee_resignation_view')
        
        # If GET request, the modal form will handle the display
        return redirect('employee_resignation_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def delete_employee_resignation_view(request, resignation_id):
    if request.user.is_authenticated:
        resignation = get_object_or_404(Resignation, id=resignation_id, employee__user=request.user)
        
        if request.method == 'POST':
            resignation.delete()
        
        return redirect('employee_resignation_view')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def update_task_status(request,task_id) :
    if request.user.is_authenticated:
        if request.method == 'POST':
            task = get_object_or_404(Task,id=task_id)
            status = request.POST.get('status')
            task.status = status
            task.save()

            return redirect('employee_dashboard')  # Redirect to the task list view
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)
 
@login_required   
def employee_update_task_status(request,task_id) :
    if request.user.is_authenticated:
        if request.method == 'POST':
            task = get_object_or_404(Task,id=task_id)
            status = request.POST.get('status')
            task.status = status
            task.save()
            Notification.objects.create(
                user=task.assigned_to.user,
                notification_type='Task',
                message=f"Task '{task.title}' has been marked as {status}"
                )
            return redirect('assign_task')
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_candidate_list(request):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        
        # Get candidates from both models
        reg_candidates = Candidate_registration.objects.filter(
            employee_name=logged_in_employee
        ).order_by('-id')
        
        cand_candidates = Candidate.objects.all(
        ).order_by('-id')
        
        # Combine both querysets
        combined_candidates = list(reg_candidates) + list(cand_candidates)
        
        # Sort by register_time (descending)
        combined_candidates.sort(key=lambda x: x.register_time, reverse=True)
        
        return render(request, 'employee/candidate-list.html', {'candidates': combined_candidates})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required    
def employee_candidate_registration(request) :
    if request.user.is_authenticated:
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
            next_follow_up_date = request.POST.get('next_follow_up_date') or None
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

        state = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", 
        "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        # Union Territories
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", 
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
        ]

        state_distict = {
            "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"],  
            "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang"],
            "Assam": ["Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong"],
            "Bihar": ["Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
            "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur", "Narayanpur"],
            "Goa": ["North Goa", "South Goa"],
            "Gujarat": ["Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad"],
            "Haryana": ["Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar"],
            "Himachal Pradesh": ["Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una"],
            "Jharkhand": ["Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum"],
            "Karnataka": ["Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir"],
            "Kerala": ["Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad"],
            "Madhya Pradesh": ["Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha"],
            "Maharashtra": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"],
            "Manipur": ["Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul"],
            "Meghalaya": ["East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills"],
            "Mizoram": ["Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip"],
            "Nagaland": ["Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto"],
            "Odisha": ["Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh"],
            "Punjab": ["Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran"],
            "Rajasthan": ["Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"],
            "Sikkim": ["East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim"],
            "Tamil Nadu": ["Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar"],
            "Telangana": ["Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri"],
            "Tripura": ["Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura"],
            "Uttar Pradesh": ["Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi"],
            "Uttarakhand": ["Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi"],
            "West Bengal": ["Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"],
            # Union Territories
            "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
            "Chandigarh": ["Chandigarh"],
            "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
            "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
            "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
            "Ladakh": ["Kargil", "Leh"],
            "Lakshadweep": ["Lakshadweep"],
            "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
        }

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
        "Software Development", "IT Support", "Web Development", "Network Administration", "Cybersecurity", "Data Science & Analytics", "Cloud Computing", "Quality Assurance (QA)","Customer Support", "Technical Support", "Voice Process", "Non-Voice Process", "Back Office Operations","Investment Banking", "Retail Banking", "Loan Processing", 
        "Risk Management", "Accounting and Auditing", "Medical Representatives", "Clinical Research", "Nursing", 
        "Medical Technicians", "Pharmacy Operations", 
        "Healthcare Administration","Teaching", "Curriculum Development", "Academic Counseling", "E-Learning Development", "Education Administration","Store Operations", "Supply Chain Management", "Sales and Merchandising", "E-commerce Operations", "Digital Marketing",
        "Production Planning", "Quality Control", "Maintenance and Repair", "Operations Management", "Inventory Management","Sales and Marketing", "Civil Engineering", "Project Management", "Interior Designing", "Surveying and Valuation","Hotel Management", "Travel Coordination", "Event Planning", "Food and Beverage Services", "Guest Relations",
        "Content Writing", "Video Editing", "Graphic Designing", "Social Media Management", "Event Production","Network Installation", "Customer Support", "Telecom Engineering", "Technical Operations", "Business Development","Logistics Coordination", "Warehouse Management", "Procurement", "Transportation Management", "Inventory Control","Market Research", "Brand Management", "Advertising Sales", "Public Relations", "Digital Marketing",
        "Recruitment", "Employee Relations", "Payroll and Benefits", "Training and Development", "HR Analytics","Corporate Law", "Compliance Auditing", "Contract Management", "Intellectual Property Rights", "Legal Advisory","Civil Engineering", "Mechanical Engineering", "Electrical Engineering", "Project Planning", "Structural Design","Automotive Design", "Production and Assembly", "Sales and Service", 
        "Supply Chain Management", "Quality Assurance","Fashion Design", "Merchandising", "Production Management", "Quality Control", "Retail Sales","Sales and Marketing", "Supply Chain Operations", "Production Management", "Quality Control", "Brand Management","Agribusiness Management", "Farm Operations", "Food Processing", "Agricultural Sales", "Quality Assurance",
        "Sales and Business Development", "Underwriting", "Claims Management", "Actuarial Services", "Policy Administration","Administrative Services", "Public Relations", "Policy Analysis", "Clerical Positions", "Field Operations","Community Development", "Fundraising", "Program Management", "Volunteer Coordination", "Policy Advocacy",
        "Renewable Energy Operations", "Power Plant Engineering", "Energy Efficiency Management", "Electrical Design", "Maintenance","Flight Operations", "Ground Staff", "Aircraft Maintenance", "Cabin Crew", "Research and Development"
        ]


        context = {
            'suggested_unique_code':suggested_unique_code,
            'districts' : districts,
            'job_sectors' : job_sectors,
            'departments' : departments,
            'state' : state,
            'state_distict' : state_distict
        }
        return render (request,'employee/candidate-registration.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)    

def get_next_unique_code():
    candidate = Candidate_registration.objects.filter(unique_code__regex=r'^EC\d{6}$').values_list('unique_code', flat=True)
    numbers = [int(re.search(r'\d{6}', unique_code).group()) for unique_code in candidate]

    if numbers:
        next_number = max(numbers) + 1  
    else:
        next_number = 1 
    return f"EC{next_number:06d}"

@login_required
def employee_candidate_profile(request, id):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        candidate = get_object_or_404(Candidate_registration.objects.prefetch_related('activities__employee'), 
                                    id=id, employee_name=logged_in_employee)
        vacancies = VacancyDetails.objects.filter(
            vacancy_status='Active'
        ).select_related('company').values(
            'id',
            'job_profile',
            'company__company_name'
        )

        if request.method == 'POST':
            # Store the original candidate data before any updates
            original_candidate = Candidate_registration.objects.get(id=id)
            changes = {}

            # Track changes for all fields at once
            fields_to_track = [
                # Personal Information
                'candidate_name', 'candidate_mobile_number', 'candidate_email_address',
                'gender', 'lead_source',
                # Candidate Details
                'candidate_alternate_mobile_number', 'preferred_location', 'origin_location',
                'qualification', 'diploma', 'sector', 'department', 'experience_year',
                'experience_month', 'current_company', 'current_working_status',
                'current_salary', 'expected_salary', 'submit_by',
                # Calling Remark
                'call_connection', 'calling_remark', 'lead_generate',
                'send_for_interview', 'next_follow_up_date',
                # Selection Record
                'selection_status', 'company_name', 'offered_salary',
                'selection_date', 'candidate_joining_date', 'emta_commission',
                'payout_date',
                'other_lead_source', 'other_qualification', 'other_working_status',
                'other_call_connection', 'other_lead_generate',
                'other_interview_status', 'other_selection_status',
                'other_origin_location'
            ]
            
            # Check for changes in all fields
            for field in fields_to_track:
                new_value = request.POST.get(field)
                old_value = getattr(original_candidate, field)
                if str(old_value) != str(new_value):
                    changes[field] = {'old': old_value, 'new': new_value}

            # Handle file uploads
            if 'candidate_photo' in request.FILES:
                changes['candidate_photo'] = {
                    'old': original_candidate.candidate_photo.name if original_candidate.candidate_photo else None,
                    'new': request.FILES['candidate_photo'].name
                }
            if 'candidate_resume' in request.FILES:
                changes['candidate_resume'] = {
                    'old': original_candidate.candidate_resume.name if original_candidate.candidate_resume else None,
                    'new': request.FILES['candidate_resume'].name
                }

            # Get list inputs and convert to string
            preferred_location = request.POST.getlist('preferred_location')
            sector = request.POST.getlist('sector')
            department = request.POST.getlist('department')
            preferred_state = request.POST.getlist('preferred_state')

            preferred_location_str = ', '.join(preferred_location)
            sector_str = ', '.join(sector)
            department_str = ', '.join(department)
            preferred_state_str = ', '.join(preferred_state)
            # Update all fields at once
            candidate.candidate_name = request.POST.get('candidate_name')
            candidate.candidate_mobile_number = request.POST.get('candidate_mobile_number')
            candidate.candidate_email_address = request.POST.get('candidate_email_address')
            candidate.gender = request.POST.get('gender')
            candidate.lead_source = request.POST.get('lead_source')

            if 'candidate_photo' in request.FILES:
                candidate.candidate_photo = request.FILES['candidate_photo']
            if 'candidate_resume' in request.FILES:
                candidate.candidate_resume = request.FILES['candidate_resume']

            # Candidate Details
            candidate.candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
            candidate.preferred_location = preferred_location_str
            candidate.preferred_state = preferred_state_str
            candidate.origin_location = request.POST.get('origin_location')
            candidate.qualification = request.POST.get('qualification')
            candidate.diploma = request.POST.get('diploma')
            candidate.sector = sector_str
            candidate.department = department_str
            candidate.experience_year = request.POST.get('experience_year')
            candidate.experience_month = request.POST.get('experience_month')
            candidate.current_company = request.POST.get('current_company')
            candidate.current_working_status = request.POST.get('current_working_status')
            candidate.current_salary = request.POST.get('current_salary')
            candidate.current_salary_type = request.POST.get('current_salary_type')
            candidate.expected_salary = request.POST.get('expected_salary')
            candidate.expected_salary_type = request.POST.get('expected_salary_type')
            candidate.submit_by = request.POST.get('submit_by')

            # Calling Remark
            candidate.call_connection = request.POST.get('call_connection')
            candidate.calling_remark = request.POST.get('calling_remark')
            candidate.lead_generate = request.POST.get('lead_generate')
            candidate.send_for_interview = request.POST.get('send_for_interview')
            candidate.next_follow_up_date = request.POST.get('next_follow_up_date') or None

            # Selection Record
            candidate.selection_status = request.POST.get('selection_status')
            candidate.company_name = request.POST.get('company_name')
            candidate.offered_salary = request.POST.get('offered_salary')
            candidate.selection_date = request.POST.get('selection_date') or None
            candidate.candidate_joining_date = request.POST.get('candidate_joining_date') or None
            candidate.emta_commission = request.POST.get('emta_commission')
            candidate.payout_date = request.POST.get('payout_date') or None
            candidate.joining_status = request.POST.get('joining_status')

            candidate.other_lead_source = request.POST.get('other_lead_source')
            candidate.other_qualification = request.POST.get('other_qualification')
            candidate.other_working_status = request.POST.get('other_working_status')
            candidate.other_call_connection = request.POST.get('other_call_connection')
            candidate.other_lead_generate = request.POST.get('other_lead_generate')
            candidate.other_interview_status = request.POST.get('other_interview_status')
            candidate.other_selection_status = request.POST.get('other_selection_status')
            candidate.other_origin_location = request.POST.get('other_origin_location')

            candidate.updated_by = logged_in_employee
            candidate.save()

            # Create activity log if there were changes
            if changes:
                CandidateActivity.objects.create(
                    candidate=candidate,
                    employee=logged_in_employee,
                    action='updated',
                    changes=changes,
                    remark="Updated via unified form"
                )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Candidate details updated successfully!'
                })
            messages.success(request, 'Candidate details updated successfully!')
            return redirect('employee_candidate_profile', id=id)
        
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
            'logged_in_employee': logged_in_employee,
            'candidate': candidate,
            'today': timezone.now().date(),
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
            'vacancies': vacancies
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, 'employee/partials/candidate_form.html', context)
            
        return render(request, 'employee/candidate-profile.html', context)
    else:
        return render(request, 'employee/404.html', status=404)
    
    
@login_required
def employee_company_registration(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            # Capture company data
            employee_name = request.POST.get('employee_name')
            company_name = request.POST.get('company_name')
            company_logo = request.FILES.get('company_logo')
            company_location = ', '.join(request.POST.getlist('company_location'))
            company_unique_code = request.POST.get('company_unique_code')
            company_email_address = request.POST.get('company_email_address')
            company_contact_person_name = request.POST.get('company_contact_person_name')
            company_contact_person_contact_details = request.POST.get('company_contact_person_contact_details')
            company_contact_person_designation = request.POST.get('company_contact_person_designation')
            interview_address = request.POST.get('interview_address')
            status_of_proposal = request.POST.get('status_of_proposal')
            invoice_generation_date = request.POST.get('invoice_generation_date') or None
            payout_date = request.POST.get('payout_date') or None
            payment_condiation = request.POST.get('payment_condiation')
            remark = request.POST.get('remark')

            # Create or update company
            company, created = Company_registration.objects.get_or_create(
                company_unique_code=company_unique_code,
                defaults={
                    'employee_name': employee_name,
                    'company_name': company_name,
                    'company_logo': company_logo,
                    'company_location': company_location,
                    'company_email_address': company_email_address,
                    'company_contact_person_name': company_contact_person_name,
                    'company_contact_person_contact_details': company_contact_person_contact_details,
                    'company_contact_person_designation': company_contact_person_designation,
                    'interview_address': interview_address,
                    'status_of_proposal': status_of_proposal,
                    'invoice_generation_date': invoice_generation_date,
                    'payout_date': payout_date,
                    'payment_condiation': payment_condiation,
                    'remark': remark,
                }
            )

            # If company exists but fields are different, update them
            if not created:
                company.employee_name = employee_name
                company.company_name = company_name
                if company_logo:
                    company.company_logo = company_logo
                company.company_location = company_location
                company.company_email_address = company_email_address
                company.company_contact_person_name = company_contact_person_name
                company.company_contact_person_contact_details = company_contact_person_contact_details
                company.company_contact_person_designation = company_contact_person_designation
                company.interview_address = interview_address
                company.status_of_proposal = status_of_proposal
                company.invoice_generation_date = invoice_generation_date
                company.payout_date = payout_date
                company.payment_condiation = payment_condiation
                company.remark = remark
                company.save()

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
        

        context = {
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
        }
        
        return render(request, 'employee/company-registration.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def search_companies(request):
    if request.user.is_authenticated:
        search_term = request.GET.get('search', '').strip()
        
        if len(search_term) >= 3:
            companies = Company_registration.objects.filter(
                company_name__icontains=search_term
            ).values('id', 'company_name', 'company_unique_code').distinct()[:10]
            
            return JsonResponse(list(companies), safe=False)
        
        return JsonResponse([], safe=False)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_company_list(request) :
    if request.user.is_authenticated:
        companys = Company_registration.objects.all().order_by('-id')
        return render(request,'employee/company-list.html',{'companys':companys})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_vacancy_list(request) :
    if request.user.is_authenticated:
        # Get all companies with their vacancy counts
        companies = Company_registration.objects.annotate(
            vacancy_count=Count('vacancies')
        ).order_by('-id')
        
        # Get all unique sector types from vacancies
        sectors = VacancyDetails.objects.values('sector_type').distinct()
        
        context = {
            'companys': companies,
            'sectors': sectors,
            'total_vacancies': VacancyDetails.objects.count()
        }
        return render(request, 'employee/vacancy-list.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_company_profile(request,id) :
    if request.user.is_authenticated:
        company = get_object_or_404(Company_registration, id=id)
        if request.method == 'POST':
            if 'company_personal_information' in request.POST:
                # Handle Employee fields
                employee_name = request.POST.get('employee_name')
                company_name = request.POST.get('company_name')
                company_location = request.POST.get('company_location')
                company_unique_code = request.POST.get('company_unique_code')
                company_logo = request.FILES.get('company_logo')
                company_email_address = request.POST.get('company_email_address')
                
                company.employee_name = employee_name
                company.company_name = company_name
                company.company_location = company_location
                company.company_unique_code = company_unique_code
                company.company_email_address=company_email_address
                company.updated_by=request.user
                if company_logo:
                    company.company_logo = company_logo
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
                
            elif 'add_vacancy' in request.POST:
                # Handle new vacancy creation
                job_profile = request.POST.get('job_profile')
                company_vacancy_unique_code = request.POST.get('company_vacancy_unique_code')
                vacancy_opening_date = request.POST.get('vacancy_opening_date') or None
                vacancy_status = request.POST.get('vacancy_status', 'Pending')
                payroll = request.POST.get('payroll')
                third_party_name = request.POST.get('third_party_name')
                job_opening_origin = request.POST.get('job_opening_origin')
                sector_type = request.POST.get('sector_type')
                department_name = request.POST.get('department_name')
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
                vacancy_closing_date = request.POST.get('vacancy_closing_date') or None
                special_instruction = request.POST.get('special_instruction')
                company_usp = request.POST.get('company_usp')
                status_of_incentive = request.POST.get('status_of_incentive')
                replacement_criteria = request.POST.get('replacement_criteria')
                
                # Payment related fields
                payment_mode = request.POST.get('payment_mode')
                company_pay_type = request.POST.get('company_pay_type')
                flat_amount = request.POST.get('flat_amount')
                percentage_of_ctc = request.POST.get('percentage_of_ctc')
                pay_per_days = request.POST.get('pay_per_days')
                salary_transfer_date = request.POST.get('salary_transfer_date') or None
                expected_payment_date = request.POST.get('expected_payment_date') or None
                candidate_salary_transfer_date = request.POST.get('candidate_salary_transfer_date') or None

                # Convert numeric fields to appropriate types
                flat_amount = float(flat_amount) if flat_amount else None
                percentage_of_ctc = float(percentage_of_ctc) if percentage_of_ctc else None
                pay_per_days = int(pay_per_days) if pay_per_days else None

                VacancyDetails.objects.create(
                    company=company,
                    job_profile=job_profile,
                    company_vacancy_unique_code=company_vacancy_unique_code,
                    vacancy_opening_date=vacancy_opening_date,
                    vacancy_status=vacancy_status,
                    payroll=payroll,
                    third_party_name=third_party_name,
                    job_opening_origin=job_opening_origin,
                    sector_type=sector_type,
                    department_name=department_name,
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
                    replacement_criteria=replacement_criteria,
                    # Payment related fields
                    payment_mode=payment_mode,
                    company_pay_type=company_pay_type,
                    flat_amount=flat_amount,
                    percentage_of_ctc=percentage_of_ctc,
                    pay_per_days=pay_per_days,
                    salary_transfer_date=salary_transfer_date,
                    expected_payment_date=expected_payment_date,
                    candidate_salary_transfer_date=candidate_salary_transfer_date,
                )
                messages.success(request, 'Vacancy added successfully!')

            elif 'edit_vacancy' in request.POST:
                # Handle vacancy editing
                vacancy_id = request.POST.get('vacancy_id')
                try:
                    vacancy = VacancyDetails.objects.get(id=vacancy_id, company=company)
                    vacancy.job_profile = request.POST.get('job_profile')
                    vacancy.company_vacancy_unique_code = request.POST.get('company_vacancy_unique_code')
                    vacancy.vacancy_opening_date = request.POST.get('vacancy_opening_date') or None
                    vacancy.vacancy_status = request.POST.get('vacancy_status', 'Pending')
                    vacancy.payroll = request.POST.get('payroll')
                    vacancy.third_party_name = request.POST.get('third_party_name')
                    vacancy.job_opening_origin = request.POST.get('job_opening_origin')
                    vacancy.sector_type = request.POST.get('sector_type')
                    vacancy.department_name = request.POST.get('department_name')
                    vacancy.fresher_status = request.POST.get('fresher_status')
                    vacancy.minimum_age = request.POST.get('minimum_age')
                    vacancy.maximum_age = request.POST.get('maximum_age')
                    vacancy.gender = request.POST.get('gender')
                    vacancy.minimum_experience = request.POST.get('minimum_experience')
                    vacancy.maximum_experience = request.POST.get('maximum_experience')
                    vacancy.minimum_education_qualification = request.POST.get('minimum_education_qualification')
                    vacancy.specialization = request.POST.get('specialization')
                    vacancy.minimum_salary_range = request.POST.get('minimum_salary_range')
                    vacancy.maximum_salary_range = request.POST.get('maximum_salary_range')
                    vacancy.vacancy_closing_date = request.POST.get('vacancy_closing_date') or None
                    vacancy.special_instruction = request.POST.get('special_instruction')
                    vacancy.company_usp = request.POST.get('company_usp')
                    vacancy.status_of_incentive = request.POST.get('status_of_incentive')
                    vacancy.replacement_criteria = request.POST.get('replacement_criteria')
                    
                    # Payment related fields
                    vacancy.payment_mode = request.POST.get('payment_mode')
                    vacancy.company_pay_type = request.POST.get('company_pay_type')
                    
                    # Convert and set numeric fields
                    # flat_amount = 
                    vacancy.flat_amount = request.POST.get('flat_amount') or None
                    
                    percentage_of_ctc = request.POST.get('percentage_of_ctc')
                    vacancy.percentage_of_ctc = float(percentage_of_ctc) if percentage_of_ctc else None
                    
                    pay_per_days = request.POST.get('pay_per_days')
                    vacancy.pay_per_days = int(pay_per_days) if pay_per_days else None
                    
                    vacancy.salary_transfer_date = request.POST.get('salary_transfer_date') or None
                    vacancy.expected_payment_date = request.POST.get('expected_payment_date') or None
                    vacancy.candidate_salary_transfer_date = request.POST.get('candidate_salary_transfer_date') or None
                    
                    vacancy.save()
                    messages.success(request, 'Vacancy updated successfully!')
                except VacancyDetails.DoesNotExist:
                    messages.error(request, 'Vacancy not found!')
                except ValueError as e:
                    messages.error(request, f'Invalid input format: {str(e)}')
                    
            elif 'delete_vacancy' in request.POST:
                # Handle vacancy deletion
                vacancy_id = request.POST.get('vacancy_id')
                try:
                    vacancy = VacancyDetails.objects.get(id=vacancy_id, company=company)
                    vacancy.delete()
                    messages.success(request, 'Vacancy deleted successfully!')
                except VacancyDetails.DoesNotExist:
                    messages.error(request, 'Vacancy not found!')
                    
            return redirect('employee_company_profile', id=id)
        
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

        vacancies = VacancyDetails.objects.filter(company=company).order_by('-id')
        
        context = {
        'districts': districts,
        'job_sectors': job_sectors,
        'departments': departments,
        'company': company,
        'vacancies' : vacancies
        }
        
        return render(request,'employee/company-profile.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_vendor_list(request) :
    if request.user.is_authenticated:
        vendors = Vendor.objects.all().order_by('-id')
        return render(request,'employee/employee-vendor-list.html',{'vendors':vendors})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_evms_candidate_list(request) :
    if request.user.is_authenticated:
        candidates = Candidate.objects.all().order_by('-id')
        return render(request,'employee/employee-evms-candidate-list.html',{'candidates':candidates})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_vendor_candidate_list(request, id):
    if request.user.is_authenticated:
        vendor = get_object_or_404(Vendor, id=id)
        candidates = Candidate.objects.filter(refer_code=vendor.refer_code).order_by('-id')
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
                return redirect('employee_vendor_candidate_list', id=vendor.id)

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
        return render(request, 'employee/employee-vendor-candidate-list.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)
@login_required
def employee_evms_candidate_profile(request, id):
    if request.user.is_authenticated:
        candidate = get_object_or_404(Candidate, id=id)
        employees = Employee.objects.all()
        vacancies = VacancyDetails.objects.filter(
            vacancy_status='Active'
        ).select_related('company').values(
            'id',
            'job_profile',
            'company__company_name'
        )
        
        if request.method == 'POST':
            if 'submit_all' in request.POST:
                # Handle Employee fields
                candidate.candidate_name = request.POST.get('candidate_name')
                candidate.employee_name = request.POST.get('employee_name')
                candidate.candidate_mobile_number = request.POST.get('candidate_mobile_number')
                candidate.candidate_email_address = request.POST.get('candidate_email_address')
                candidate.gender = request.POST.get('gender')
                candidate.lead_source = request.POST.get('lead_source')
                if 'candidate_photo' in request.FILES:
                    candidate.candidate_photo = request.FILES.get('candidate_photo')
                if 'candidate_resume' in request.FILES:
                    candidate.candidate_resume = request.FILES.get('candidate_resume')
                candidate.submit_by = request.POST.get('submit_by')
                candidate.candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
                candidate.preferred_location = request.POST.get('preferred_location')
                candidate.origin_location = request.POST.get('origin_location')
                candidate.qualification = request.POST.get('qualification')
                candidate.diploma = request.POST.get('diploma')
                candidate.sector = request.POST.get('sector')
                candidate.department = request.POST.get('department')
                candidate.experience_year = request.POST.get('experience_year')
                candidate.experience_month = request.POST.get('experience_month')
                candidate.current_company = request.POST.get('current_company')
                candidate.current_working_status = request.POST.get('current_working_status')
                candidate.current_salary = request.POST.get('current_salary')
                candidate.expected_salary = request.POST.get('expected_salary')
                candidate.submit_by = request.POST.get('submit_by')

                candidate.call_connection = request.POST.get('call_connection')
                candidate.calling_remark = request.POST.get('calling_remark')
                candidate.lead_generate = request.POST.get('lead_generate')
                candidate.send_for_interview = request.POST.get('send_for_interview')
                candidate.next_follow_up_date = request.POST.get('next_follow_up_date') or None
                candidate.submit_by = request.POST.get('submit_by')

                candidate.selection_status = request.POST.get('selection_status')
                candidate.company_name = request.POST.get('company_name')
                candidate.offered_salary = request.POST.get('offered_salary')
                candidate.selection_date = request.POST.get('selection_date') or None
                candidate.candidate_joining_date = request.POST.get('candidate_joining_date') or None
                candidate.emta_commission = request.POST.get('emta_commission')
                candidate.payout_date = request.POST.get('payout_date')

                candidate.vendor_commission = request.POST.get('vendor_commission')
                candidate.vendor_payout_date = request.POST.get('vendor_payout_date') or None
                candidate.commission_generation_date = request.POST.get('commission_generation_date') or None
                candidate.vendor_commission_status = request.POST.get('vendor_commission_status')
                candidate.vendor_payment_remark = request.POST.get('vendor_payment_remark')
                candidate.payment_done_by = request.POST.get('payment_done_by')
                candidate.payment_done_by_date = request.POST.get('payment_done_by_date') or None
                if 'submit_recipt' in request.FILES:
                    candidate.submit_recipt = request.FILES.get('submit_recipt')
                candidate.save()
                
            elif 'submit_vendor_related_data' in request.POST:
                # Handle form submission for bank details
                candidate.vendor_commission = request.POST.get('vendor_commission')
                candidate.vendor_payout_date = request.POST.get('vendor_payout_date') or None
                candidate.commission_generation_date = request.POST.get('commission_generation_date') or None
                candidate.vendor_commission_status = request.POST.get('vendor_commission_status')
                candidate.vendor_payment_remark = request.POST.get('vendor_payment_remark')
                candidate.payment_done_by = request.POST.get('payment_done_by')
                candidate.payment_done_by_date = request.POST.get('payment_done_by_date') or None
                if 'submit_recipt' in request.FILES:
                    candidate.submit_recipt = request.FILES.get('submit_recipt')
                candidate.save()
                messages.success(request, 'Vendor releted details updated successfully!')

            return redirect('employee_evms_candidate_profile', id=id)
        context = {
            'candidate': candidate,
            'employees' : employees,
            'vacancies' : vacancies,
            'activities': candidate.activities.all().order_by('-timestamp'),
        }
        return render(request,'employee/evms-candidate-profile.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def evms_vendor_candidate_profile(request,id) :
    if request.user.is_authenticated:
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
        return render(request,'employee/evms-vendor-candidate-profile.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def birthday_and_anniversary_today(request):
    if request.user.is_authenticated:
        today = date.today()

        # Get all employees
        employees = EmployeeAdditionalInfo.objects.filter(date_of_birth__isnull=False)

        # Filter for birthdays today
        birthdays_today = []
        for emp in employees:
            if emp.date_of_birth:
                dob_this_year = emp.date_of_birth.replace(year=today.year)
                if dob_this_year == today:
                    birthdays_today.append(emp)

        # Filter for work anniversaries today
        anniversaries_today = []
        for emp in employees:
            joining_date = emp.employee.joining_date
            if joining_date:
                anniversary_this_year = joining_date.replace(year=today.year)
                if anniversary_this_year == today:
                    anniversaries_today.append(emp)

        response_data = {
            "birthdays_today": [
                {
                    "name": f"{emp.employee.first_name} {emp.employee.last_name}",
                    "designation": emp.employee.designation,
                    "photo_url": emp.employee.employee_photo.url if emp.employee.employee_photo else "",  # Ensure the photo field is properly handled
                    "date_of_birth": emp.date_of_birth.strftime("%d %b %Y"),
                }
                for emp in birthdays_today
            ],
            "anniversaries_today": [
                {
                    "name": f"{emp.employee.first_name} {emp.employee.last_name}",
                    "designation": emp.employee.designation,
                    "photo_url": emp.employee.employee_photo.url if emp.employee.employee_photo else "",
                    "joining_date": emp.employee.joining_date.strftime("%d %b %Y"),
                }
                for emp in anniversaries_today
            ],
        }

        return JsonResponse(response_data)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def same_designation_list_json(request):
    if request.user.is_authenticated:
        # Get the logged-in user's employee record
        try:
            logged_in_employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            return JsonResponse({'error': 'Employee record not found for the logged-in user'}, status=404)

        # Get the designation and department of the logged-in employee
        designation = logged_in_employee.designation
        department = logged_in_employee.department

        # Query for all employees with the same designation and department, excluding the logged-in employee
        same_department_and_designation_employees = Employee.objects.filter(
            department=department
        ).exclude(id=logged_in_employee.id)

        # Serialize employee data to JSON format
        employee_list = [
            {
                'id': emp.id,
                'name': f"{emp.first_name} {emp.last_name}",
                'designation': emp.designation,
                'department': emp.department,
                'email': emp.user.email if emp.user else None,
            }
            for emp in same_department_and_designation_employees
        ]

        # Return the list in JSON format
        return JsonResponse({
            'designation': designation,
            'department': department,
            'employees': employee_list,
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def ticket_view(request):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        if request.method == 'POST':
            # Generate a unique ticket number
            ticket_number = f"TIC-{uuid.uuid4().hex[:8].upper()}"
            
            # Capture form data from POST request
            ticket_name = request.POST.get('ticket_name')
            ticket_description = request.POST.get('ticket_description')
            ticket_status = request.POST.get('ticket_status')
            ticket_priority = request.POST.get('ticket_priority')
            ticket_category = request.POST.get('ticket_category')
            ticket_assign_to = Employee.objects.get(id=int(request.POST.get('ticket_assign_to')))
            ticket_remark = request.POST.get('ticket_remark')

            # Handle date fields safely
            ticket_created_date = request.POST.get('ticket_created_date', '').strip()
            ticket_closed_date = request.POST.get('ticket_closed_date', '').strip()

            # Convert to datetime format, or set to None if empty
            ticket_created_date = parse_datetime(ticket_created_date) if ticket_created_date else None
            ticket_closed_date = parse_datetime(ticket_closed_date) if ticket_closed_date else None

            # Create a new Ticket record
            Ticket.objects.create(
                ticket_number=ticket_number,
                ticket_name=ticket_name,
                ticket_description=ticket_description,
                ticket_status=ticket_status,
                ticket_priority=ticket_priority,
                ticket_category=ticket_category,
                ticket_assign_to=ticket_assign_to,
                ticket_assign_by=logged_in_employee,
                ticket_created_date=ticket_created_date,
                ticket_closed_date=ticket_closed_date,
                ticket_remark=ticket_remark
            )

            # Redirect to the same page after saving
            return redirect('ticket_view')

        # Get all tickets and employees in the IT department
        tickets = Ticket.objects.all()
        employees = Employee.objects.filter(department="IT")  

        return render(request, 'employee/ticket.html', {'tickets': tickets, 'employees': employees})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)



def employee_performance_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get time period filter (default to week)
    period = request.GET.get('period', 'week')
    
    # Get the logged-in employee's name
    logged_in_employee = Employee.objects.get(user=request.user)
    today = datetime.now().date()
    
    # Calculate date ranges based on period
    if period == 'today':
        start_date = today
        end_date = today
        previous_start = today - timedelta(days=1)
        previous_end = today - timedelta(days=1)
        trend_interval = 'hourly'
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        previous_start = start_date - timedelta(weeks=1)
        previous_end = start_date - timedelta(days=1)
        trend_interval = 'daily'
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = (start_date.replace(month=start_date.month+1) - timedelta(days=1)
                   if start_date.month < 12 
                   else start_date.replace(year=start_date.year+1, month=1) - timedelta(days=1))
        previous_start = (start_date - timedelta(days=1)).replace(day=1)
        previous_end = start_date - timedelta(days=1)
        trend_interval = 'weekly'
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year+1) - timedelta(days=1)
        previous_start = start_date.replace(year=start_date.year-1)
        previous_end = start_date - timedelta(days=1)
        trend_interval = 'monthly'
    
    # Base queryset for this employee
    current_qs = Candidate_registration.objects.filter(
        employee_name=logged_in_employee,
        register_time__date__range=[start_date, end_date]
    )
    previous_qs = Candidate_registration.objects.filter(
        employee_name=logged_in_employee,
        register_time__date__range=[previous_start, previous_end]
    )
    
    # Calculate trend data based on period
    trend_data = []
    trend_labels = []
    
    if trend_interval == 'hourly':
        for hour in range(0, 24):
            trend_labels.append(f"{hour}:00")
            trend_data.append(
                current_qs.filter(
                    register_time__hour=hour
                ).count()
            )
    elif trend_interval == 'daily':
        trend_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        trend_labels = [date.strftime('%a %d') for date in trend_dates]
        trend_data = [
            current_qs.filter(register_time__date=date).count()
            for date in trend_dates
        ]
    elif trend_interval == 'weekly':
        weeks_in_month = 5  # Maximum weeks to show
        for i in range(weeks_in_month):
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            if week_start.month != start_date.month:
                break
            trend_labels.append(f"Week {i+1}")
            trend_data.append(
                current_qs.filter(
                    register_time__date__range=[week_start, week_end]
                ).count()
            )
    elif trend_interval == 'monthly':
        for month in range(1, 13):  # Fixed: Only loop through valid months 1-12
            month_start = start_date.replace(month=month, day=1)
            # Handle December -> January transition
            if month == 12:
                month_end = month_start.replace(year=month_start.year+1, month=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month+1) - timedelta(days=1)
            
            # Ensure we don't go beyond current date
            if month_start > today:
                break
                
            if month_end > today:
                month_end = today
                
            trend_labels.append(month_start.strftime('%b'))
            trend_data.append(
                current_qs.filter(
                    register_time__date__range=[month_start, month_end]
                ).count()
            )
    
    # Performance metrics
    total_current = current_qs.count()
    total_previous = previous_qs.count()
    
    metrics = {
        'period': period,
        'total_candidates': total_current,
        'total_change': calculate_change(total_current, total_previous),
        
        'selected_candidates': current_qs.filter(selection_status='Selected').count(),
        'selection_rate': calculate_percentage(
            current_qs.filter(selection_status='Selected').count(),
            total_current
        ),
        'selection_change': calculate_change(
            current_qs.filter(selection_status='Selected').count(),
            previous_qs.filter(selection_status='Selected').count()
        ),
        
        'interview_candidates': current_qs.filter(send_for_interview='Yes').count(),
        'interview_rate': calculate_percentage(
            current_qs.filter(send_for_interview='Yes').count(),
            total_current
        ),
        'interview_change': calculate_change(
            current_qs.filter(send_for_interview='Yes').count(),
            previous_qs.filter(send_for_interview='Yes').count()
        ),
        
        'lead_generation': current_qs.filter(lead_generate='Yes').count(),
        'lead_change': calculate_change(
            current_qs.filter(lead_generate='Yes').count(),
            previous_qs.filter(lead_generate='Yes').count()
        ),
        
        'today_candidates': Candidate_registration.objects.filter(
            employee_name=logged_in_employee,
            register_time__date=today
        ).count(),
    }
    
    # Status distribution
    status_counts = current_qs.values('selection_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    status_distribution = []
    for status in status_counts:
        status_distribution.append({
            'status': status['selection_status'],
            'count': status['count'],
            'percentage': calculate_percentage(status['count'], total_current)
        })
    
    # Call connection stats
    call_stats = {
        'connected': current_qs.filter(call_connection='Yes').count(),
        'failed': current_qs.exclude(call_connection='Yes').exclude(call_connection__isnull=True).count(),
        'connect_rate': calculate_percentage(
            current_qs.filter(call_connection='Yes').count(),
            current_qs.exclude(call_connection__isnull=True).count()
        ),
        'fail_rate': calculate_percentage(
            current_qs.exclude(call_connection='Yes').exclude(call_connection__isnull=True).count(),
            current_qs.exclude(call_connection__isnull=True).count()
        ),
        'breakdown': get_call_breakdown(current_qs, previous_qs)
    }
    
    # Recent candidates (last 5)
    recent_candidates = current_qs.order_by('-register_time')[:5]
    
    # Today's candidates (for today view)
    today_candidates = Candidate_registration.objects.filter(
        employee_name=logged_in_employee,
        register_time__date=today
    ).order_by('-register_time')
    
    # Prepare chart data
    chart_data = {
        'trend_data': trend_data,
        'trend_labels': trend_labels,
        'status_series': [s['count'] for s in status_distribution],
        'status_labels': [s['status'] for s in status_distribution]
    }
    
    return render(request, 'employee/employee-performance-dashboard.html', {
        'metrics': metrics,
        'status_distribution': status_distribution,
        'call_stats': call_stats,
        'recent_candidates': recent_candidates,
        'today_candidates': today_candidates,
        'trend_data': chart_data['trend_data'],
        'trend_labels': chart_data['trend_labels'],
        'status_series': chart_data['status_series'],
        'status_labels': chart_data['status_labels'],
        'period': period,
        'today': today,
    })

def calculate_percentage(part, whole):
    return round((part / whole) * 100, 1) if whole > 0 else 0

def calculate_change(current, previous):
    return round(((current - previous) / previous * 100), 1) if previous > 0 else 0

def get_call_breakdown(current_qs, previous_qs):
    statuses = ['Yes', 'No', 'Busy', 'Not Reachable', 'Wrong Number']
    breakdown = []
    
    for status in statuses:
        current_count = current_qs.filter(call_connection=status).count()
        previous_count = previous_qs.filter(call_connection=status).count()
        
        breakdown.append({
            'status': status,
            'count': current_count,
            'percentage': calculate_percentage(
                current_count,
                current_qs.exclude(call_connection__isnull=True).count()
            ),
            'trend': calculate_change(current_count, previous_count)
        })
    
    return breakdown
    
@login_required
def employee_chart_data(request):
    if request.user.is_authenticated:
        today1 = now().date()
        logged_in_employee = request.user.employee  # Assuming Employee is linked to User

        # Fetch data counts
        total_call_count = Candidate_registration.objects.filter(
            register_time__date=today1, employee_name=logged_in_employee
        ).count()
        
        total_connected_call = Candidate_registration.objects.filter(
            call_connection='Yes', register_time__date=today1, employee_name=logged_in_employee
        ).count()
        
        total_non_connected_call = Candidate_registration.objects.filter(
            call_connection='No', register_time__date=today1, employee_name=logged_in_employee
        ).count()
        
        total_lead_generate = Candidate_registration.objects.filter(
            lead_generate='Yes', register_time__date=today1, employee_name=logged_in_employee
        ).count()
        
        total_placement = Candidate_registration.objects.filter(
            selection_status='Selected', register_time__date=today1, employee_name=logged_in_employee
        ).count()

        # Prepare JSON response
        data = {
            "series": [total_call_count, total_connected_call, total_lead_generate, total_placement, total_non_connected_call],
            "labels": ["Total Calls", "Connected Calls", "Leads Generated", "Placements", "Non-Connected Calls"]
        }

        return JsonResponse(data)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def overall_employee_chart_data(request):
    if request.user.is_authenticated:
        today = now().date()
        logged_in_employee = request.user.employee  # Assuming Employee is linked to User

        # Get the filter parameter from the request (default to 'week')
        filter_type = request.GET.get('filter', 'week')

        # Determine the start date based on the filter type
        if filter_type == 'week':
            start_date = today - timedelta(days=7)
        elif filter_type == 'month':
            start_date = today - timedelta(days=30)
        elif filter_type == 'year':
            start_date = today - timedelta(days=365)
        else:
            return JsonResponse({'error': 'Invalid filter type'}, status=400)

        # Fetch data counts
        total_call_count = Candidate_registration.objects.filter(
            register_time__date__gte=start_date, register_time__date__lte=today, employee_name=logged_in_employee
        ).count()

        total_connected_call = Candidate_registration.objects.filter(
            call_connection='Yes', register_time__date__gte=start_date, register_time__date__lte=today, employee_name=logged_in_employee
        ).count()

        total_non_connected_call = Candidate_registration.objects.filter(
            call_connection='No', register_time__date__gte=start_date, register_time__date__lte=today, employee_name=logged_in_employee
        ).count()

        total_lead_generate = Candidate_registration.objects.filter(
            lead_generate='Yes', register_time__date__gte=start_date, register_time__date__lte=today, employee_name=logged_in_employee
        ).count()

        total_placement = Candidate_registration.objects.filter(
            selection_status='Selected', register_time__date__gte=start_date, register_time__date__lte=today, employee_name=logged_in_employee
        ).count()

        # Prepare JSON response with counts in labels
        data = {
            "series": [total_call_count, total_connected_call, total_lead_generate, total_placement, total_non_connected_call],
            "labels": [
                f"Total Calls ({total_call_count})",
                f"Connected Calls ({total_connected_call})",
                f"Leads Generated ({total_lead_generate})",
                f"Placements ({total_placement})",
                f"Non-Connected Calls ({total_non_connected_call})"
            ],
            "filter": filter_type
        }

        return JsonResponse(data)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def each_employee_chart_data(request):
    if request.user.is_authenticated:
        today = now().date()
        logged_in_employee = request.user.employee  # Get the logged-in employee
        filter_type = request.GET.get("filter", "week")  # Default filter is 'week'

        if filter_type == "week":
            date_trunc = TruncWeek("register_time")  # Group by week
        elif filter_type == "month":
            date_trunc = TruncMonth("register_time")  # Group by month
        elif filter_type == "year":
            date_trunc = TruncYear("register_time")  # Group by year
        else:
            return JsonResponse({"error": "Invalid filter"}, status=400)

        # Fetch aggregated data based on the selected filter
        data_queryset = (
            Candidate_registration.objects.filter(employee_name=logged_in_employee)
            .annotate(period=date_trunc)
            .values("period")
            .annotate(
                total_calls=Count("id"),
                connected_calls=Count("id", filter=models.Q(call_connection="Yes")),
                leads_generated=Count("id", filter=models.Q(lead_generate="Yes"))
            )
            .order_by("period")
        )

        # Format data for the chart
        labels = []
        total_calls = []
        connected_calls = []
        leads_generated = []

        for entry in data_queryset:
            labels.append(entry["period"].strftime("%Y-%m-%d"))  # Convert date format
            total_calls.append(entry["total_calls"])
            connected_calls.append(entry["connected_calls"])
            leads_generated.append(entry["leads_generated"])

        # Return JSON response
        return JsonResponse({
            "labels": labels,
            "total_calls": total_calls,
            "connected_calls": connected_calls,
            "leads_generated": leads_generated
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def get_revenue_placement_data(request):
    if request.user.is_authenticated:
        filter_type = request.GET.get("filter", "week")

        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        start_of_month = today.replace(day=1)  # 1st of the month
        start_of_year = today.replace(month=1, day=1)  # 1st Jan

        if filter_type == "week":
            start_date = start_of_week
        elif filter_type == "month":
            start_date = start_of_month
        elif filter_type == "year":
            start_date = start_of_year
        else:
            return JsonResponse({"error": "Invalid filter"}, status=400)

        # Fetch placement dates
        placements_qs = Candidate_registration.objects.filter(register_time__date__gte=start_date)
        placements_by_date = (
            placements_qs.values("register_time__date").annotate(count=Sum(1))  # Count placements per date
        )

        # Fetch revenue
        total_revenue = placements_qs.aggregate(total_earning=Sum("emta_commission"))["total_earning"] or 0.0

        # Generate labels and data
        labels = sorted(set(p["register_time__date"] for p in placements_by_date))
        placement_data = [next((p["count"] for p in placements_by_date if p["register_time__date"] == date), 0) for date in labels]
        revenue_data = [total_revenue] * len(labels)  # Apply same revenue across dates

        return JsonResponse({
            "placements": placement_data,
            "revenue": revenue_data,
            "labels": [date.strftime("%d-%m-%Y") for date in labels]
        })
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_leave_details(request):
    if request.user.is_authenticated:
        """Return attendance data for the logged-in user from joining date to today."""
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        employee = Employee.objects.filter(user=request.user).first()
        if not employee:
            return JsonResponse({"error": "Employee data not found"}, status=404)

        today = localtime().date()
        start_date = employee.joining_date  # Start from employee's joining date

        # Get attendance records
        present_days = 0
        late_days = 0
        absent_days = 0
        leave_days = 0
        half_days = 0

        # Fetch holidays
        holidays = set(Holiday.objects.values_list('date', flat=True))

        delta = timedelta(days=1)
        current_date = start_date

        while current_date <= today:
            # Skip holidays and Sundays
            if current_date in holidays or current_date.weekday() == 6:
                current_date += delta
                continue

            # Check for leave requests
            if LeaveRequest.objects.filter(
                employee=employee, start_date__lte=current_date, end_date__gte=current_date, status="Approved"
            ).exists():
                leave_days += 1

            else:
                sessions = EmployeeSession.objects.filter(user=employee.user, punch_in_time__date=current_date)
                total_time = sum((session.total_time for session in sessions if session.total_time), timedelta())

                # Convert total time to hours
                total_hours = total_time.total_seconds() / 3600

                if total_hours < 4 and total_hours > 0:
                    half_days += 1
                elif sessions.exists():
                    first_punch_in = sessions.earliest('punch_in_time').punch_in_time
                    punch_in_hour = first_punch_in.hour
                    punch_in_minute = first_punch_in.minute

                    # Determine late attendance
                    if punch_in_hour > 10 or (punch_in_hour == 10 and punch_in_minute > 10):
                        late_days += 1
                    else:
                        present_days += 1
                else:
                    absent_days += 1

            current_date += delta

        # JSON response with chart data
        data = {
            "labels": ["On Time", "Late Attendance", "Absent", "Leave", "Half Day"],
            "series": [present_days, late_days, absent_days, leave_days, half_days],
        }
        return JsonResponse(data)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_attendance_details(request):
    if request.user.is_authenticated:
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        employee = Employee.objects.filter(user=request.user).first()
        if not employee:
            return JsonResponse({"error": "Employee data not found"}, status=404)

        today = localtime().date()
        start_date = employee.joining_date
        total_leaves = 24  # Defined total leaves

        # Fetch holidays
        holidays = set(Holiday.objects.values_list('date', flat=True))

        # Fetch leave requests
        approved_leaves = LeaveRequest.objects.filter(employee=employee, status="Approved").count()
        pending_requests = LeaveRequest.objects.filter(employee=employee, status="Hold").count()

        total_days = (today - start_date).days + 1  # Total days including today
        worked_days = 0
        absent_days = 0
        
        delta = timedelta(days=1)
        current_date = start_date

        while current_date <= today:
            # Skip holidays and Sundays
            if current_date in holidays or current_date.weekday() == 6:
                current_date += delta
                continue

            # Check if employee has worked on the day
            sessions = EmployeeSession.objects.filter(user=employee.user, punch_in_time__date=current_date)
            if sessions.exists():
                worked_days += 1
            else:
                absent_days += 1
            
            current_date += delta

        # JSON response
        data = {
            "Total Leaves": total_leaves,
            "Taken": approved_leaves,
            "Absent": absent_days,
            "Request": pending_requests,
            "Worked Days": worked_days,
            "Loss of Pay": absent_days  # Assuming loss of pay is equal to absent days
        }
        return JsonResponse(data)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

def format_decimal_hours(td):
    """Convert timedelta to decimal hours format (e.g., 8.36)"""
    total_seconds = td.total_seconds()
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) / 60
    return f"{hours:.0f}.{int(minutes):02}"  # Example: 8.36

def format_integer_hours(td):
    """Convert timedelta to integer hours (e.g., 16)"""
    return f"{int(td.total_seconds() // 3600)}"  # Example: 16

def format_hours_minutes(td):
    """Convert timedelta to '12h 36m' format"""
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    return f"{hours}h {minutes}m"  # Example: 12h 36m

def calculate_work_hours(sessions):
    """Calculate total working hours from employee sessions."""
    return sum((session.total_time for session in sessions if session.total_time), timedelta())

def work_hours_summary(request):
    if request.user.is_authenticated:
        user = request.user
        today = now().date()
        week_start = today - timedelta(days=today.weekday())  # Monday as start of the week
        month_start = today.replace(day=1)  # Start of the month

        # Fetch today's sessions
        today_sessions = EmployeeSession.objects.filter(user=user, punch_in_time__date=today)

        # Get first punch-in and last punch-out
        first_punch_in = today_sessions.order_by("punch_in_time").first()
        last_punch_out = today_sessions.order_by("-punch_out_time").first()

        # Calculate total logged-in time (first punch-in to last punch-out)
        if first_punch_in and last_punch_out and last_punch_out.punch_out_time:
            total_hours_today = last_punch_out.punch_out_time - first_punch_in.punch_in_time
        else:
            total_hours_today = timedelta()
            
        # Calculate another total logged-in time (first punch-in to last punch-out)
        if first_punch_in and last_punch_out and last_punch_out.punch_out_time:
            another_today_total_working_time = last_punch_out.punch_out_time - first_punch_in.punch_in_time
        else:
            another_today_total_working_time = timedelta()

        # Actual working hours (sum of session working times)
        today_productive_hours = calculate_work_hours(today_sessions)

        # Break time = Total logged-in time - Actual working time
        today_break_hours = max(total_hours_today - today_productive_hours, timedelta())

        # Weekly and Monthly work hours
        week_sessions = EmployeeSession.objects.filter(user=user, punch_in_time__date__gte=week_start)
        month_sessions = EmployeeSession.objects.filter(user=user, punch_in_time__date__gte=month_start)

        total_hours_week = calculate_work_hours(week_sessions)
        total_hours_month = calculate_work_hours(month_sessions)

        # Overtime calculations (Anything over 9 hours)
        today_overtime = max(today_productive_hours - timedelta(hours=9), timedelta())
        month_overtime = sum(
            (max(session.total_time - timedelta(hours=9), timedelta()) for session in month_sessions if session.total_time),
            timedelta()
        )

        response_data = {
            "total_hours_today": format_decimal_hours(total_hours_today),  # Total logged-in time in decimal format
            "total_hours_week": format_integer_hours(total_hours_week),  # 16 format
            "total_hours_month": format_integer_hours(total_hours_month),  # 16 format
            "month_overtime": format_integer_hours(month_overtime),  # 16 format
            "today_productive_hours": format_hours_minutes(today_productive_hours),  # Working hours (e.g., 7h 45m)
            "today_break_hours": format_hours_minutes(today_break_hours),  # Break time (e.g., 1h 15m)
            "today_overtime": format_hours_minutes(today_overtime),  # Overtime (e.g., 0h 0m)
            "another_today_total_working_time": format_hours_minutes(another_today_total_working_time)
        }

        return JsonResponse(response_data)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_selected_candidate(request) :
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        candidates = Candidate_registration.objects.filter(employee_name=logged_in_employee, selection_status='Selected').order_by('-id')
        context = {
            'candidates': candidates
        }
        return render(request,'employee/selected-candidate.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_follow_up_candidate(request):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        today = timezone.now().date()
        date_range_start = today - timedelta(days=2)  # 25th if today is 27th
        date_range_end = today + timedelta(days=3)    # 30th if today is 27th
        
        candidates = Candidate_registration.objects.filter(
            employee_name=logged_in_employee,
            next_follow_up_date__isnull=False,
            next_follow_up_date__gte=date_range_start,
            next_follow_up_date__lte=date_range_end
        ).order_by('next_follow_up_date')  # Order by follow-up date
        
        context = {
            'candidates': candidates,
            'today': today
        }
        return render(request, 'employee/follow-up-candidate.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def employee_generated_leads(request):
    if request.user.is_authenticated:
        logged_in_employee = Employee.objects.get(user=request.user)
        candidates = Candidate_registration.objects.filter(employee_name=logged_in_employee, lead_generate='Yes').order_by('-id')
        context = {
            'candidates': candidates
        }
        return render(request,'employee/employee-lead-generate.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def evms_vendor_paylist(request):
    if request.user.is_authenticated:
        # Get current month and year
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        
        # Filter candidates with refer_code, pending commission, and payout date in current month
        remaining_pays = Candidate.objects.filter(
            vendor_commission_status='Pending',
            selection_status='Selected',
            refer_code__isnull=False,
            vendor_payout_date__month=current_month,
            vendor_payout_date__year=current_year
        ).order_by('-id')
        
        # Prepare data for template
        candidates = []
        for candidate in remaining_pays:
            try:
                vendor = Vendor.objects.get(refer_code=candidate.refer_code)
                vendor_name = f"{vendor.user.first_name} {vendor.user.last_name}"
            except Vendor.DoesNotExist:
                vendor_name = "Unknown Vendor"
            
            # Add vendor name to candidate object (we'll use this in template)
            candidate.vendor_name = vendor_name
            candidates.append(candidate)
        
        context = {
            'candidates': candidates
        }
        return render(request, 'employee/evms-vendor-paylist.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def evms_vendor_transaction_history(request):
    if request.user.is_authenticated:
        
        # Filter candidates with refer_code, pending commission, and payout date in current month
        remaining_pays = Candidate.objects.filter(
            vendor_commission_status__in=['Complete', 'Failed'],
            selection_status='Selected',
            refer_code__isnull=False,
        ).order_by('-id')
        
        # Prepare data for template
        candidates = []
        for candidate in remaining_pays:
            try:
                vendor = Vendor.objects.get(refer_code=candidate.refer_code)
                vendor_name = f"{vendor.user.first_name} {vendor.user.last_name}"
            except Vendor.DoesNotExist:
                vendor_name = "Unknown Vendor"
            
            # Add vendor name to candidate object (we'll use this in template)
            candidate.vendor_name = vendor_name
            candidates.append(candidate)
        
        context = {
            'candidates': candidates
        }
        return render(request, 'employee/vendor-transaction-history.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)

@login_required
def export_vendors_to_excel(request):
    if request.user.is_authenticated:
        # Get all vendors with related data
        vendors = Vendor.objects.all().select_related(
            'vendor_profile_details',
            'vendor_bussiness_details',
            'vendor_bank_details'
        )
        
        # Prepare data for Excel
        data = []
        for vendor in vendors:
            data.append({
                'Vendor Code': vendor.refer_code,
                'First Name': vendor.user.first_name,
                'Last Name': vendor.user.last_name,
                'Email': vendor.user.email,
                'Mobile Number': vendor.mobile_number,
                'Date of Birth': vendor.date_of_birth,
                'Verification Status': vendor.profileVerification,
                'Total Commission': vendor.total_commission_received,
                
                # Profile Details
                'Address': vendor.vendor_profile_details.address if hasattr(vendor, 'vendor_profile_details') else '',
                'Gender': vendor.vendor_profile_details.gender if hasattr(vendor, 'vendor_profile_details') else '',
                'Aadhar Number': vendor.vendor_profile_details.adhar_card_number if hasattr(vendor, 'vendor_profile_details') else '',
                'PAN Number': vendor.vendor_profile_details.pan_card_number if hasattr(vendor, 'vendor_profile_details') else '',
                'Location': vendor.vendor_profile_details.location if hasattr(vendor, 'vendor_profile_details') else '',
                
                # Business Details
                'Shop Name': vendor.vendor_bussiness_details.shop_name if hasattr(vendor, 'vendor_bussiness_details') else '',
                'Shop Address': vendor.vendor_bussiness_details.shop_address if hasattr(vendor, 'vendor_bussiness_details') else '',
                'Business Type': vendor.vendor_bussiness_details.busness_type if hasattr(vendor, 'vendor_bussiness_details') else '',
                'Gumasta Number': vendor.vendor_bussiness_details.Gumasta_number if hasattr(vendor, 'vendor_bussiness_details') else '',
                'GST Number': vendor.vendor_bussiness_details.gst_number if hasattr(vendor, 'vendor_bussiness_details') else '',
                'Business PAN': vendor.vendor_bussiness_details.Bpan_number if hasattr(vendor, 'vendor_bussiness_details') else '',
                'MSME Number': vendor.vendor_bussiness_details.MSME_number if hasattr(vendor, 'vendor_bussiness_details') else '',
                'Contact Number': vendor.vendor_bussiness_details.Contact_number if hasattr(vendor, 'vendor_bussiness_details') else '',
                'Business Email': vendor.vendor_bussiness_details.Busness_email if hasattr(vendor, 'vendor_bussiness_details') else '',
                
                # Bank Details
                'Account Holder': vendor.vendor_bank_details.account_holder_name if hasattr(vendor, 'vendor_bank_details') else '',
                'Account Number': vendor.vendor_bank_details.account_number if hasattr(vendor, 'vendor_bank_details') else '',
                'Bank Name': vendor.vendor_bank_details.bank_name if hasattr(vendor, 'vendor_bank_details') else '',
                'IFSC Code': vendor.vendor_bank_details.ifs_code if hasattr(vendor, 'vendor_bank_details') else '',
                'MICR Code': vendor.vendor_bank_details.micr_code if hasattr(vendor, 'vendor_bank_details') else '',
                'Account Type': vendor.vendor_bank_details.account_type if hasattr(vendor, 'vendor_bank_details') else '',
                'Payout Date': vendor.vendor_bank_details.preffered_payout_date if hasattr(vendor, 'vendor_bank_details') else '',
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create HTTP response with Excel file
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="vendors_export.xlsx"'
        
        # Write DataFrame to Excel
        df.to_excel(response, index=False, sheet_name='Vendors')
        
        return response
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'employee/404.html', status=404)
    
@login_required
def candidate_chat_list(request, candidate_id):
    candidate = get_object_or_404(Candidate_registration, id=candidate_id)
    logged_in_employee = Employee.objects.get(user=request.user)
    
    # Handle form submission
    if request.method == 'POST':
        chat_message = request.POST.get('chat_message')
        chat_type = request.POST.get('chat_type', 'internal')
        is_important = request.POST.get('is_important') == 'on'
        next_followup = request.POST.get('next_followup') or None
        attachment = request.FILES.get('attachment')
        
        Candidate_chat.objects.create(
            candidate=candidate,
            chat_message=chat_message,
            employee_name=logged_in_employee,
            chat_type=chat_type,
            is_important=is_important,
            next_followup=next_followup,
            attachment=attachment
        )
        messages.success(request, 'Chat record added successfully!')
        return redirect('candidate_chat_list', candidate_id=candidate_id)
    
    # Filter chats
    chat_type_filter = request.GET.get('type', 'all')
    if chat_type_filter == 'all':
        chats = Candidate_chat.objects.filter(candidate=candidate)
    elif chat_type_filter == 'important':
        chats = Candidate_chat.objects.filter(candidate=candidate, is_important=True)
    else:
        chats = Candidate_chat.objects.filter(candidate=candidate, chat_type=chat_type_filter)
    
    # Pagination
    paginator = Paginator(chats.order_by('-chat_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'candidate': candidate,
        'chats': page_obj,
        'chat_type_filter': chat_type_filter,
    }
    return render(request, 'employee/candidate_chat_list.html', context)

@login_required
def delete_chat(request, pk):
    chat = get_object_or_404(Candidate_chat, pk=pk)
    candidate_id = chat.candidate.id
    chat.delete()
    messages.success(request, 'Chat record deleted successfully!')
    return redirect('candidate_chat_list', candidate_id=candidate_id)

@login_required
def interview_list(request, candidate_id):
    candidate = get_object_or_404(Candidate_registration, id=candidate_id)
    companys = Company_registration.objects.all()
    
    if request.method == 'POST':
        if 'send_email' in request.POST:
            # Handle email sending
            interview_id = request.POST.get('interview_id')
            interview = get_object_or_404(Candidate_Interview, id=interview_id)
            send_interview_email(request, interview)
            messages.success(request, 'Interview details sent to candidate!')
            return redirect('interview_list', candidate_id=candidate_id)
        
        # Handle form submission
        interview_date = request.POST.get('interview_date')
        interview_time = request.POST.get('interview_time')
        company_name = request.POST.get('company_name')
        job_position = request.POST.get('job_position')
        status = request.POST.get('status')
        interview_mode = request.POST.get('interview_mode')
        notes = request.POST.get('notes')
        
        interview = Candidate_Interview(
            candidate=candidate,
            interview_date=interview_date,
            interview_time=interview_time,
            company_name=company_name,
            job_position=job_position,
            status=status,
            interview_mode=interview_mode,
            notes=notes,
            interviewer_name=request.POST.get('interviewer_name'),
            interviewer_email=request.POST.get('interviewer_email'),
            interviewer_phone=request.POST.get('interviewer_phone'),
            location=request.POST.get('location'),
            meeting_link=request.POST.get('meeting_link'),
            feedback=request.POST.get('feedback'),
            rating=request.POST.get('rating') or None,
            is_technical=request.POST.get('is_technical') == 'on',
            duration=request.POST.get('duration', 60),
            requirements=request.POST.get('requirements'),
            attachment=request.FILES.get('attachment')
        )
        interview.save()
        messages.success(request, 'Interview scheduled successfully!')
        return redirect('interview_list', candidate_id=candidate_id)
    
    # Filter interviews
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'all':
        interviews = candidate.interviews.all()
    else:
        interviews = candidate.interviews.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(interviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'candidate': candidate,
        'interviews': page_obj,
        'status_filter': status_filter,
        'status_choices': Candidate_Interview.INTERVIEW_STATUS,
        'mode_choices': Candidate_Interview.INTERVIEW_MODE,
        'companys' : companys
    }
    return render(request, 'employee/candidate_interview_list.html', context)

@login_required
def send_interview_email(request, interview):
    """Helper function to send interview details email"""
    subject = f"Interview Scheduled - {interview.company_name}"
    
    context = {
        'interview': interview,
        'candidate': interview.candidate,
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/interview_scheduled.html', context)
    
    # Create email
    email = EmailMessage(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [interview.candidate.candidate_email_address],
    )
    email.content_subtype = "html"  # Set content type to HTML
    
    # Attach file if exists
    if interview.attachment:
        email.attach_file(interview.attachment.path)
    
    # Send email
    email.send()

@login_required
def interview_detail(request, interview_id):
    interview = get_object_or_404(Candidate_Interview, id=interview_id)
    companys = Company_registration.objects.all()
    
    if request.method == 'POST':
        # Handle update
        interview.interview_date = request.POST.get('interview_date')
        interview.interview_time = request.POST.get('interview_time')
        interview.company_name = request.POST.get('company_name')
        interview.job_position = request.POST.get('job_position')
        interview.status = request.POST.get('status')
        interview.interview_mode = request.POST.get('interview_mode')
        interview.notes = request.POST.get('notes')
        interview.interviewer_name = request.POST.get('interviewer_name')
        interview.interviewer_email = request.POST.get('interviewer_email')
        interview.interviewer_phone = request.POST.get('interviewer_phone')
        interview.location = request.POST.get('location')
        interview.meeting_link = request.POST.get('meeting_link')
        interview.feedback = request.POST.get('feedback')
        interview.rating = request.POST.get('rating') or None
        interview.is_technical = request.POST.get('is_technical') == 'on'
        interview.duration = request.POST.get('duration', 60)
        interview.requirements = request.POST.get('requirements')
        
        if 'attachment' in request.FILES:
            interview.attachment = request.FILES['attachment']
        
        interview.save()
        messages.success(request, 'Interview updated successfully!')
        return redirect('interview_detail', interview_id=interview.id)
    
    context = {
        'interview': interview,
        'status_choices': Candidate_Interview.INTERVIEW_STATUS,
        'mode_choices': Candidate_Interview.INTERVIEW_MODE,
        'companys' : companys
    }
    return render(request, 'employee/candidate_interview_detail.html', context)

@login_required
def delete_interview(request, interview_id):
    interview = get_object_or_404(Candidate_Interview, id=interview_id)
    candidate_id = interview.candidate.id
    interview.delete()
    messages.success(request, 'Interview deleted successfully!')
    return redirect('interview_list', candidate_id=candidate_id)

@login_required
def company_communication_list(request, company_id):
    company = get_object_or_404(Company_registration, id=company_id)
    
    if request.method == 'POST':
        if 'send_email' in request.POST:
            # Handle email sending
            communication_id = request.POST.get('communication_id')
            communication = get_object_or_404(company_communication, id=communication_id)
            send_communication_email(request, communication)
            messages.success(request, 'Communication details sent successfully!')
            return redirect('company_communication_list', company_id=company_id)
        
        # Handle form submission
        communication = company_communication(
            company=company,
            contact_person=request.POST.get('contact_person'),
            designation=request.POST.get('designation'),
            contact_email=request.POST.get('contact_email'),
            contact_phone=request.POST.get('contact_phone'),
            communication_date=request.POST.get('communication_date'),
            communication_type=request.POST.get('communication_type'),
            subject=request.POST.get('subject'),
            communication_details=request.POST.get('communication_details'),
            follow_up_date=request.POST.get('follow_up_date') or None,
            priority=request.POST.get('priority', 'medium'),
            outcome=request.POST.get('outcome'),
            employee_name=request.user.get_full_name() or request.user.username,
            attachment=request.FILES.get('attachment')
        )
        communication.save()
        messages.success(request, 'Communication record added successfully!')
        return redirect('company_communication_list', company_id=company_id)
    
    # Filter communications
    type_filter = request.GET.get('type', 'all')
    priority_filter = request.GET.get('priority', 'all')
    
    communications = company_communication.objects.filter(company=company)
    
    if type_filter != 'all':
        communications = communications.filter(communication_type=type_filter)
    if priority_filter != 'all':
        communications = communications.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(communications.order_by('-communication_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'communications': page_obj,
        'type_filter': type_filter,
        'priority_filter': priority_filter,
        'communication_types': company_communication.COMMUNICATION_TYPES,
        'priority_choices': company_communication.PRIORITY_CHOICES,
    }
    return render(request, 'employee/company_communication_list.html', context)

@login_required
def company_communication_detail(request, communication_id):
    communication = get_object_or_404(company_communication, id=communication_id)
    
    if request.method == 'POST':
        # Handle update
        communication.contact_person = request.POST.get('contact_person')
        communication.designation = request.POST.get('designation')
        communication.contact_email = request.POST.get('contact_email')
        communication.contact_phone = request.POST.get('contact_phone')
        communication.communication_date = request.POST.get('communication_date')
        communication.communication_type = request.POST.get('communication_type')
        communication.subject = request.POST.get('subject')
        communication.communication_details = request.POST.get('communication_details')
        communication.follow_up_date = request.POST.get('follow_up_date') or None
        communication.priority = request.POST.get('priority', 'medium')
        communication.outcome = request.POST.get('outcome')
        
        if 'attachment' in request.FILES:
            communication.attachment = request.FILES['attachment']
        
        communication.save()
        messages.success(request, 'Communication record updated successfully!')
        return redirect('company_communication_detail', communication_id=communication.id)
    
    context = {
        'communication': communication,
        'communication_types': company_communication.COMMUNICATION_TYPES,
        'priority_choices': company_communication.PRIORITY_CHOICES,
    }
    return render(request, 'employee/company_communication_detail.html', context)

@login_required
def delete_company_communication(request, communication_id):
    communication = get_object_or_404(company_communication, id=communication_id)
    company_id = communication.company.id
    communication.delete()
    messages.success(request, 'Communication record deleted successfully!')
    return redirect('company_communication_list', company_id=company_id)

@login_required
def send_communication_email(request, communication):
    """Helper function to send communication details email"""
    subject = f"Communication Record: {communication.subject}"
    
    context = {
        'communication': communication,
        'company': communication.company,
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/company_communication_record.html', context)
    
    recipients = [communication.contact_email]
    if communication.company.company_email_address:
        recipients.append(communication.company.company_email_address)
    
    # Create email
    email = EmailMessage(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        cc=[request.user.email] if request.user.email else None,
    )
    email.content_subtype = "html"
    
    # Attach file if exists
    if communication.attachment:
        email.attach_file(communication.attachment.path)
    
    # Send email
    email.send()
    
@login_required
def company_contacts_list(request, company_id):
    company = get_object_or_404(Company_registration, id=company_id)
    
    if request.method == 'POST':
        if 'send_email' in request.POST:
            # Handle email sending
            contact_id = request.POST.get('contact_id')
            contact = get_object_or_404(Company_spoke_person, id=contact_id)
            # Add your email sending logic here
            messages.success(request, f'Email sent to {contact.name} successfully!')
            return redirect('company_contacts_list', company_id=company_id)
        
        # Handle form submission
        contact = Company_spoke_person(
            company=company,
            name=request.POST.get('name'),
            designation=request.POST.get('designation'),
            department=request.POST.get('department'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            location=request.POST.get('location'),
            is_primary=request.POST.get('is_primary') == 'on',
            priority=request.POST.get('priority', 'medium'),
            status=request.POST.get('status', 'active'),
            notes=request.POST.get('notes'),
            last_contact_date=request.POST.get('last_contact_date') or None,
            next_followup=request.POST.get('next_followup') or None,
            created_by=request.user,
            updated_by=request.user
        )
        contact.save()
        messages.success(request, 'Contact person added successfully!')
        return redirect('company_contacts_list', company_id=company_id)
    
    # Filter contacts
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    is_primary_filter = request.GET.get('is_primary', 'all')
    
    contacts = Company_spoke_person.objects.filter(company=company)
    
    if status_filter != 'all':
        contacts = contacts.filter(status=status_filter)
    if priority_filter != 'all':
        contacts = contacts.filter(priority=priority_filter)
    if is_primary_filter != 'all':
        contacts = contacts.filter(is_primary=(is_primary_filter == 'true'))
    
    # Pagination
    paginator = Paginator(contacts.order_by('-is_primary', '-priority', 'name'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'contacts': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'is_primary_filter': is_primary_filter,
        'status_choices': Company_spoke_person.STATUS_CHOICES,
        'priority_choices': Company_spoke_person.PRIORITY_CHOICES,
    }
    return render(request, 'employee/contacts_list.html', context)

@login_required
def company_contact_detail(request, contact_id):
    contact = get_object_or_404(Company_spoke_person, id=contact_id)
    
    if request.method == 'POST':
        # Handle update
        contact.name = request.POST.get('name')
        contact.designation = request.POST.get('designation')
        contact.department = request.POST.get('department')
        contact.email = request.POST.get('email')
        contact.phone = request.POST.get('phone')
        contact.location = request.POST.get('location')
        contact.is_primary = request.POST.get('is_primary') == 'on'
        contact.priority = request.POST.get('priority', 'medium')
        contact.status = request.POST.get('status', 'active')
        contact.notes = request.POST.get('notes')
        contact.last_contact_date = request.POST.get('last_contact_date') or None
        contact.next_followup = request.POST.get('next_followup') or None
        contact.updated_by = request.user
        contact.save()
        
        messages.success(request, 'Contact person updated successfully!')
        return redirect('company_contact_detail', contact_id=contact.id)
    
    context = {
        'contact': contact,
        'status_choices': Company_spoke_person.STATUS_CHOICES,
        'priority_choices': Company_spoke_person.PRIORITY_CHOICES,
    }
    return render(request, 'employee/contact_detail.html', context)

@login_required
def delete_company_contact(request, contact_id):
    contact = get_object_or_404(Company_spoke_person, id=contact_id)
    company_id = contact.company.id
    contact.delete()
    messages.success(request, 'Contact person deleted successfully!')
    return redirect('company_contacts_list', company_id=company_id)


@login_required
def employee_evms_candidate_chat_list(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    logged_in_employee = Employee.objects.get(user=request.user)
    
    # Handle form submission
    if request.method == 'POST':
        chat_message = request.POST.get('chat_message')
        chat_type = request.POST.get('chat_type', 'internal')
        is_important = request.POST.get('is_important') == 'on'
        next_followup = request.POST.get('next_followup') or None
        attachment = request.FILES.get('attachment')
        
        EVMS_Candidate_chat.objects.create(
            candidate=candidate,
            chat_message=chat_message,
            employee_name=logged_in_employee,
            chat_type=chat_type,
            is_important=is_important,
            next_followup=next_followup,
            attachment=attachment,
            created_by=request.user
        )
        messages.success(request, 'Chat record added successfully!')
        return redirect('employee_evms_candidate_chat_list', candidate_id=candidate_id)
    
    # Filter chats
    chat_type_filter = request.GET.get('type', 'all')
    if chat_type_filter == 'all':
        chats = EVMS_Candidate_chat.objects.filter(candidate=candidate)
    elif chat_type_filter == 'important':
        chats = EVMS_Candidate_chat.objects.filter(candidate=candidate, is_important=True)
    else:
        chats = EVMS_Candidate_chat.objects.filter(candidate=candidate, chat_type=chat_type_filter)
    
    # Pagination
    paginator = Paginator(chats.order_by('-chat_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'candidate': candidate,
        'chats': page_obj,
        'chat_type_filter': chat_type_filter,
    }
    return render(request, 'employee/evms_candidate_chat_list.html', context)

@login_required
def employee_evms_delete_chat(request, pk):
    chat = get_object_or_404(EVMS_Candidate_chat, pk=pk)
    candidate_id = chat.candidate.id
    chat.delete()
    messages.success(request, 'Chat record deleted successfully!')
    return redirect('employee_evms_candidate_chat_list', candidate_id=candidate_id)

@login_required
def employee_evms_interview_list(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    companys = Company_registration.objects.all()
    vacancies = VacancyDetails.objects.filter(vacancy_status='Active').order_by('-id')
    
    if request.method == 'POST':
        if 'send_email' in request.POST:
            # Handle email sending
            interview_id = request.POST.get('interview_id')
            interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id)
            send_interview_email(request, interview)
            messages.success(request, 'Interview details sent to candidate!')
            return redirect('employee_evms_interview_list', candidate_id=candidate_id)
        
        # Handle form submission
        interview_date = request.POST.get('interview_date')
        interview_time = request.POST.get('interview_time')
        company_name = request.POST.get('company_name')
        job_position = request.POST.get('job_position')
        status = request.POST.get('status')
        interview_mode = request.POST.get('interview_mode')
        notes = request.POST.get('notes')
        
        interview = EVMS_Candidate_Interview(
            candidate=candidate,
            interview_date=interview_date,
            interview_time=interview_time,
            company_name=company_name,
            job_position=job_position,
            status=status,
            interview_mode=interview_mode,
            notes=notes,
            interviewer_name=request.POST.get('interviewer_name'),
            interviewer_email=request.POST.get('interviewer_email'),
            interviewer_phone=request.POST.get('interviewer_phone'),
            location=request.POST.get('location'),
            meeting_link=request.POST.get('meeting_link'),
            feedback=request.POST.get('feedback'),
            rating=request.POST.get('rating') or None,
            is_technical=request.POST.get('is_technical') == 'on',
            duration=request.POST.get('duration', 60),
            requirements=request.POST.get('requirements'),
            attachment=request.FILES.get('attachment'),
            created_by=request.user
        )
        interview.save()
        messages.success(request, 'Interview scheduled successfully!')
        return redirect('employee_evms_interview_list', candidate_id=candidate_id)
    
    # Filter interviews
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'all':
        interviews = candidate.interviews.all()
    else:
        interviews = candidate.interviews.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(interviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'candidate': candidate,
        'interviews': page_obj,
        'status_filter': status_filter,
        'status_choices': EVMS_Candidate_Interview.INTERVIEW_STATUS,
        'mode_choices': EVMS_Candidate_Interview.INTERVIEW_MODE,
        'companys' : companys,
        'vacancies' : vacancies
    }
    return render(request, 'employee/evms_candidate_interview_list.html', context)

@login_required
def send_evms_interview_email(request, interview):
    """Helper function to send interview details email"""
    subject = f"Interview Scheduled - {interview.company_name}"
    
    context = {
        'interview': interview,
        'candidate': interview.candidate,
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/interview_scheduled.html', context)
    
    # Create email
    email = EmailMessage(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [interview.candidate.candidate_email_address],
    )
    email.content_subtype = "html"  # Set content type to HTML
    
    # Attach file if exists
    if interview.attachment:
        email.attach_file(interview.attachment.path)
    
    # Send email
    email.send()

@login_required
def employee_evms_interview_detail(request, interview_id):
    interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id)
    companys = Company_registration.objects.all()
    
    if request.method == 'POST':
        # Handle update
        interview.interview_date = request.POST.get('interview_date')
        interview.interview_time = request.POST.get('interview_time')
        interview.company_name = request.POST.get('company_name')
        interview.job_position = request.POST.get('job_position')
        interview.status = request.POST.get('status')
        interview.interview_mode = request.POST.get('interview_mode')
        interview.notes = request.POST.get('notes')
        interview.interviewer_name = request.POST.get('interviewer_name')
        interview.interviewer_email = request.POST.get('interviewer_email')
        interview.interviewer_phone = request.POST.get('interviewer_phone')
        interview.location = request.POST.get('location')
        interview.meeting_link = request.POST.get('meeting_link')
        interview.feedback = request.POST.get('feedback')
        interview.rating = request.POST.get('rating') or None
        interview.is_technical = request.POST.get('is_technical') == 'on'
        interview.duration = request.POST.get('duration', 60)
        interview.requirements = request.POST.get('requirements')
        interview.updated_by=request.user
        
        if 'attachment' in request.FILES:
            interview.attachment = request.FILES['attachment']
        
        interview.save()
        messages.success(request, 'Interview updated successfully!')
        return redirect('employee_evms_interview_detail', interview_id=interview.id)
    
    context = {
        'interview': interview,
        'status_choices': EVMS_Candidate_Interview.INTERVIEW_STATUS,
        'mode_choices': EVMS_Candidate_Interview.INTERVIEW_MODE,
        'companys' : companys
    }
    return render(request, 'employee/evms_candidate_interview_detail.html', context)


@login_required
def employee_evms_delete_interview(request, interview_id):
    interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id)
    candidate_id = interview.candidate.id
    interview.delete()
    messages.success(request, 'Interview deleted successfully!')
    return redirect('employee_evms_interview_list', candidate_id=candidate_id)