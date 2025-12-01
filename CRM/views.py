from django.shortcuts import render, redirect,get_object_or_404
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.db.models import Sum, Min, Max
from App.models import *
import pandas as pd
from django.core.files.base import ContentFile
from io import BytesIO
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import csv
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import Q
from itertools import chain
from django.urls import reverse
from datetime import datetime, timedelta


# Create your views here.

def crm_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("admin_calls_list")  
        else:
            messages.error(request, "Invalid credentials or insufficient permissions.")
    return render(request, "crm/admin-login.html")

def crm_admin_logout(request):
    logout(request)
    return redirect(crm_admin_login)

from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from itertools import chain
# from .models import Candidate_registration, Candidate, Candidate_Interview, EVMS_Candidate_Interview
from django.utils import timezone


from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from itertools import chain
# from .models import Candidate_registration, Candidate, Candidate_Interview, EVMS_Candidate_Interview
from django.utils import timezone

def user_not_found_view(request):
    return render(request, 'crm/404.html', status=404)


@login_required(login_url='/crm/404/')
def crm_dashboard(request):
    """
    Renders the CRM dashboard with various performance metrics.
    Handles filtering by time period and custom date ranges.
    Combines data from two different candidate models.
    """
    if request.user.is_staff or request.user.is_superuser:
        # Time period filter
        period = request.GET.get('period', 'day')
        custom_start = request.GET.get('start_date')
        custom_end = request.GET.get('end_date')

        # Initialize date ranges
        today = datetime.now().date()
        start_date = None
        end_date = None

        # Handle custom date range
        if custom_start and custom_end:
            try:
                start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(custom_end, '%Y-%m-%d').date() + timedelta(days=1)
                period = 'custom'
            except ValueError:
                pass
        else:
            # Calculate standard period date ranges
            if period == 'day':
                start_date = today
                end_date = today + timedelta(days=1)
            elif period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=7)
            elif period == 'month':
                start_date = today.replace(day=1)
                end_date = (start_date.replace(month=start_date.month + 1)
                            if start_date.month < 12
                            else start_date.replace(year=start_date.year + 1, month=1))
            elif period == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = start_date.replace(year=start_date.year + 1)

        # --- Dashboard Card and other data preparation (as per your original code) ---
        today_follow_up = timezone.now().date()
        date_range_start = today_follow_up - timedelta(days=2)
        date_range_end = today_follow_up + timedelta(days=3)

        interview_detail_reg = Candidate_Interview.objects.filter(
            interview_date_time__date=today,
            status__in=['scheduled', 'rescheduled']
        ).order_by('interview_date_time')
        interview_detail_can = EVMS_Candidate_Interview.objects.filter(
            interview_date_time__date=today,
            status__in=['scheduled', 'rescheduled']
        ).order_by('interview_date_time')
        interview_detail = list(chain(interview_detail_reg, interview_detail_can))
        interview_detail.sort(key=lambda x: x.interview_date_time if x.interview_date_time else datetime.min.date(), reverse=False)

        follow_up_candidates_reg = Candidate_registration.objects.filter(
            next_follow_up_date_time__isnull=False,
            next_follow_up_date_time__gte=date_range_start,
            next_follow_up_date_time__lte=date_range_end
        ).order_by('next_follow_up_date_time')
        follow_up_candidates_can = Candidate.objects.filter(
            next_follow_up_date_time__isnull=False,
            next_follow_up_date_time__gte=date_range_start,
            next_follow_up_date_time__lte=date_range_end
        ).order_by('next_follow_up_date_time')
        follow_up_candidates = list(chain(follow_up_candidates_reg, follow_up_candidates_can))
        follow_up_candidates.sort(key=lambda x: x.next_follow_up_date_time if x.next_follow_up_date_time else datetime.min.date(), reverse=False)

        # Base querysets for both databases for the current period
        current_qs_reg = Candidate_registration.objects.all()
        current_qs_can = Candidate.objects.all()

        if start_date and end_date:
            current_qs_reg = current_qs_reg.filter(register_time__date__range=[start_date, end_date - timedelta(days=1)])
            current_qs_can = current_qs_can.filter(register_time__date__range=[start_date, end_date - timedelta(days=1)])

        # Employee performance metrics for both databases (for cards)
        employee_performance_reg = list(current_qs_reg.values('employee_name').annotate(
            total_candidates=Count('id'),
            selected_candidates=Count('id', filter=Q(selection_status='Selected')),
            pending_candidates=Count('id', filter=Q(selection_status='Pending')),
            rejected_candidates=Count('id', filter=Q(selection_status='Rejected'))
        ).order_by('-total_candidates'))

        employee_performance_can = list(current_qs_can.values('employee_name').annotate(
            total_candidates=Count('id'),
            selected_candidates=Count('id', filter=Q(selection_status='Selected')),
            pending_candidates=Count('id', filter=Q(selection_status='Pending')),
            rejected_candidates=Count('id', filter=Q(selection_status='Rejected'))
        ).order_by('-total_candidates'))
        
        employee_performance_dict = {}
        for entry in employee_performance_reg + employee_performance_can:
            emp = entry['employee_name']
            if emp not in employee_performance_dict:
                employee_performance_dict[emp] = entry
            else:
                employee_performance_dict[emp]['total_candidates'] += entry['total_candidates']
                employee_performance_dict[emp]['selected_candidates'] += entry['selected_candidates']
                employee_performance_dict[emp]['pending_candidates'] += entry['pending_candidates']
                employee_performance_dict[emp]['rejected_candidates'] += entry['rejected_candidates']
        employee_performance = sorted(employee_performance_dict.values(), key=lambda x: x['total_candidates'], reverse=True)

        lead_generation_reg = list(current_qs_reg.filter(lead_generate__in=['Hot', 'Converted']).values('employee_name').annotate(
            lead_count=Count('id')
        ).order_by('-lead_count'))

        lead_generation_can = list(current_qs_can.filter(lead_generate__in=['Hot', 'Converted']).values('employee_name').annotate(
            lead_count=Count('id')
        ).order_by('-lead_count'))

        lead_generation_dict = {}
        for entry in lead_generation_reg + lead_generation_can:
            emp = entry['employee_name']
            if emp not in lead_generation_dict:
                lead_generation_dict[emp] = entry
            else:
                lead_generation_dict[emp]['lead_count'] += entry['lead_count']
        lead_generation = sorted(lead_generation_dict.values(), key=lambda x: x['lead_count'], reverse=True)
        total_lead_generation = sum([entry['lead_count'] for entry in lead_generation])
        
        call_connection_reg = list(current_qs_reg.exclude(call_connection__isnull=True).exclude(call_connection__exact='').values(
            'employee_name', 'call_connection'
        ).annotate(
            count=Count('id')
        ).order_by('employee_name', '-count'))
        call_connection_can = list(current_qs_can.exclude(call_connection__isnull=True).exclude(call_connection__exact='').values(
            'employee_name', 'call_connection'
        ).annotate(
            count=Count('id')
        ).order_by('employee_name', '-count'))
        
        call_connection_dict = {}
        for entry in call_connection_reg + call_connection_can:
            key = (entry['employee_name'], entry['call_connection'])
            if key not in call_connection_dict:
                call_connection_dict[key] = entry
            else:
                call_connection_dict[key]['count'] += entry['count']
        call_connection = sorted(call_connection_dict.values(), key=lambda x: (x['employee_name'], -x['count']))
        
        interview_candidates = current_qs_reg.filter(send_for_interview__in=['Scheduled', 'Rescheduled']).count() + current_qs_can.filter(send_for_interview__in=['Scheduled', 'Rescheduled']).count()
        
        # --- NEW & MODIFIED CODE FOR THE TABLE DATA ---
        
        # Helper function to calculate time ago string
        def time_ago_string(dt):
            if not dt:
                return "N/A"
            now = timezone.now()
            diff = now - dt
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"

        # Aggregate all unique employee names from both databases
        employee_names_reg = list(current_qs_reg.values_list('employee_name', flat=True).distinct())
        employee_names_can = list(current_qs_can.values_list('employee_name', flat=True).distinct())
        all_employees = sorted(list(set(employee_names_reg + employee_names_can)))

        # Prepare a dictionary to hold the aggregated data for each employee
        employee_table_data = {}
        for emp_name in all_employees:
            employee_table_data[emp_name] = {
                'emp_name': emp_name,
                # 'emp_code': 'N/A', # Placeholder if not available in your models
                'total_calls_made': 0,
                'connected_calls': 0,
                'connection_rate': '0.0%',
                'leads_generated': 0,
                'last_call_made_time_ago': 'N/A',
                'last_action_timestamp': None, # New field for JavaScript
                'has_last_call': False, # New flag for JavaScript
            }

        # Fetch and merge call data
        call_data_reg = list(current_qs_reg.filter(employee_name__in=all_employees).values('employee_name', 'call_connection').annotate(count=Count('id')))
        call_data_can = list(current_qs_can.filter(employee_name__in=all_employees).values('employee_name', 'call_connection').annotate(count=Count('id')))
        
        for entry in call_data_reg + call_data_can:
            emp_name = entry['employee_name']
            if emp_name in employee_table_data:
                count = entry['count']
                employee_table_data[emp_name]['total_calls_made'] += count
                if entry['call_connection'] in ['Yes', 'Connected']:
                    employee_table_data[emp_name]['connected_calls'] += count

        # Fetch the most recent register_time for each employee
        last_action_times_reg = current_qs_reg.values('employee_name').annotate(last_action_time=Max('register_time'))
        last_action_times_can = current_qs_can.values('employee_name').annotate(last_action_time=Max('register_time'))
        
        last_action_times_dict = {}
        for entry in list(last_action_times_reg) + list(last_action_times_can):
            emp_name = entry['employee_name']
            last_action_time = entry['last_action_time']
            if emp_name not in last_action_times_dict or last_action_time > last_action_times_dict[emp_name]:
                last_action_times_dict[emp_name] = last_action_time

        # Calculate connection rate and last call time string
        for emp_name, data in employee_table_data.items():
            total_calls = data['total_calls_made']
            connected_calls = data['connected_calls']
            if total_calls > 0:
                rate = (connected_calls / total_calls) * 100
                data['connection_rate'] = f"{rate:.1f}%"
            
            # Populate the last call made time using the last action time
            last_action_dt = last_action_times_dict.get(emp_name)
            if last_action_dt:
                data['last_call_made_time_ago'] = time_ago_string(last_action_dt)
                data['last_action_timestamp'] = last_action_dt.isoformat() # ISO format for JS
                data['has_last_call'] = True

        # Fetch and merge lead data
        lead_data_reg = list(current_qs_reg.filter(employee_name__in=all_employees, lead_generate__in=['Hot', 'Converted']).values('employee_name').annotate(count=Count('id')))
        lead_data_can = list(current_qs_can.filter(employee_name__in=all_employees, lead_generate__in=['Hot', 'Converted']).values('employee_name').annotate(count=Count('id')))
        
        for entry in lead_data_reg + lead_data_can:
            emp_name = entry['employee_name']
            if emp_name in employee_table_data:
                employee_table_data[emp_name]['leads_generated'] += entry['count']

        # Convert the dictionary back to a list for template iteration
        employee_table_list = sorted(list(employee_table_data.values()), key=lambda x: x['total_calls_made'], reverse=True)

        # --- End of new code for table data ---

        # Calculate other dashboard cards (unchanged)
        def get_status_comparison(current_count, previous_count):
            if previous_count > 0:
                change = ((current_count - previous_count) / previous_count) * 100
                return f"{change:+.1f}%"
            elif current_count > 0:
                return "+100.0%"
            else:
                return "0.0%"

        prev_qs_reg = Candidate_registration.objects.none()
        prev_qs_can = Candidate.objects.none()
        if period != 'custom':
             # Calculate previous period date ranges for comparison
            if period == 'day':
                prev_start = start_date - timedelta(days=1)
                prev_end = end_date - timedelta(days=1)
            elif period == 'week':
                prev_start = start_date - timedelta(days=7)
                prev_end = end_date - timedelta(days=7)
            elif period == 'month':
                prev_start = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
                prev_end = start_date.replace(day=1)
            elif period == 'year':
                prev_start = start_date.replace(year=start_date.year - 1)
                prev_end = end_date.replace(year=end_date.year - 1)
            
            prev_qs_reg = Candidate_registration.objects.filter(register_time__date__range=[prev_start, prev_end - timedelta(days=1)])
            prev_qs_can = Candidate.objects.filter(register_time__date__range=[prev_start, prev_end - timedelta(days=1)])

        total_candidates = current_qs_reg.count() + current_qs_can.count()
        selected_candidates = (current_qs_reg.filter(selection_status='Selected').count() +
                               current_qs_can.filter(selection_status='Selected').count())
        pending_candidates = (current_qs_reg.filter(selection_status='Pending').count() +
                              current_qs_can.filter(selection_status='Pending').count())
        rejected_candidates = (current_qs_reg.filter(selection_status='Rejected').count() +
                               current_qs_can.filter(selection_status='Rejected').count())
        prev_total_candidates = prev_qs_reg.count() + prev_qs_can.count()

        status_comparison = {
            'day': get_status_comparison(total_candidates, prev_total_candidates if period == 'day' else 0),
            'week': get_status_comparison(total_candidates, prev_total_candidates if period == 'week' else 0),
            'month': get_status_comparison(total_candidates, prev_total_candidates if period == 'month' else 0),
            'year': get_status_comparison(total_candidates, prev_total_candidates if period == 'year' else 0),
        }
        
        current_status_reg_list = list(current_qs_reg.values('selection_status').annotate(count=Count('id')))
        current_status_can_list = list(current_qs_can.values('selection_status').annotate(count=Count('id')))
        current_status_dict = {}
        for entry in current_status_reg_list + current_status_can_list:
            status = entry['selection_status']
            if status not in current_status_dict:
                current_status_dict[status] = entry
            else:
                current_status_dict[status]['count'] += entry['count']
        current_status = sorted(current_status_dict.values(), key=lambda x: -x['count'])


        # Prepare context for template
        context = {
            # New context for the table
            'employee_table_data': employee_table_list,
            
            # Existing context variables
            'employee_performance': employee_performance,
            'lead_generation': lead_generation,
            'total_lead_generation': total_lead_generation,
            'call_connection': call_connection,
            'interview_candidates': interview_candidates,
            'current_status': current_status,
            'status_comparison': status_comparison,
            'period': period,
            'start_date': start_date,
            'end_date': end_date - timedelta(days=1) if end_date else None,
            'custom_start': custom_start,
            'custom_end': custom_end,
            'total_candidates': total_candidates,
            'selected_candidates': selected_candidates,
            'pending_candidates': pending_candidates,
            'rejected_candidates': rejected_candidates,
            'interview_detail': interview_detail,
            'follow_up_candidates': follow_up_candidates,
        }
        return render(request, 'crm/crm-dashboard.html', context)
    else:
        return render(request, 'crm/404.html', status=404)



@login_required(login_url='/crm/404/')
def employee_candidates_list(request, employee_name, filter_type):
    """
    Renders a page with a list of all candidates for a specific employee,
    filtered by the selected time period and performance category.
    """
    if request.user.is_staff or request.user.is_superuser:
        # Get filtering data from URL parameters
        period = request.GET.get('period', 'all')
        custom_start_str = request.GET.get('start_date')
        custom_end_str = request.GET.get('end_date')

        start_date = None
        end_date = None
        date_range_display = "All Time"

        if custom_start_str and custom_end_str:
            try:
                start_date = datetime.strptime(custom_start_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(custom_end_str, '%Y-%m-%d').date() + timedelta(days=1)
                date_range_display = f"{start_date.strftime('%b %d, %Y')} - {datetime.strptime(custom_end_str, '%Y-%m-%d').date().strftime('%b %d, %Y')}"
            except (ValueError, TypeError):
                pass
        else:
            today = datetime.now().date()
            if period == 'day':
                start_date = today
                end_date = today + timedelta(days=1)
                date_range_display = "Today"
            elif period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=7)
                date_range_display = "This Week"
            elif period == 'month':
                start_date = today.replace(day=1)
                end_date = (start_date.replace(month=start_date.month + 1)
                            if start_date.month < 12
                            else start_date.replace(year=start_date.year + 1, month=1))
                date_range_display = "This Month"
            elif period == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = start_date.replace(year=start_date.year + 1)
                date_range_display = "This Year"

        # Initialize base querysets for both models
        candidates_reg = Candidate_registration.objects.filter(employee_name=employee_name)
        candidates_can = Candidate.objects.filter(employee_name=employee_name)

        # Apply date filters
        if start_date and end_date:
            candidates_reg = candidates_reg.filter(register_time__date__range=[start_date, end_date - timedelta(days=1)])
            candidates_can = candidates_can.filter(register_time__date__range=[start_date, end_date - timedelta(days=1)])

        # Apply additional filters based on filter_type
        filter_title = ""
        if filter_type == 'leads':
            candidates_reg = candidates_reg.filter(lead_generate__in=['Hot', 'Converted'])
            candidates_can = candidates_can.filter(lead_generate__in=['Hot', 'Converted'])
            filter_title = "Lead Generation"
        elif filter_type == 'calls':
            candidates_reg = candidates_reg.all
            candidates_can = candidates_can.filter(Q(call_connection='Yes') | Q(call_connection='Connected') | Q(call_connection='Not Connected'))
            filter_title = "Call Connections"
        elif filter_type == 'performance':
            filter_title = "Performance"
        else:
            filter_title = "All Candidates"

        # Combine the querysets and sort
        candidates = list(chain(candidates_reg, candidates_can))
        candidates.sort(key=lambda x: x.register_time if x.register_time else datetime.min, reverse=True)
        
        # --- DEBUGGING STATEMENT ---
        # This will print the number of candidates found to your console
        print(f"Employee Candidates List - Employee: {employee_name}, Filter: {filter_type}, Period: {period}, Candidates found: {len(candidates)}")
        # --- END OF DEBUGGING STATEMENT ---

        context = {
            'employee_name': employee_name,
            'filter_title': filter_title,
            'candidates': candidates,
            'period': period,
            'date_range_display': date_range_display,
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
            'end_date': (end_date - timedelta(days=1)).strftime('%Y-%m-%d') if end_date else '',
            'filter_type': filter_type,
        }
        return render(request, 'crm/employee-candidates-list.html', context)
    else:
        return render(request, 'crm/404.html', status=404)


import datetime as dt
from django.db.models.fields.files import FieldFile # Make sure this is imported!


import datetime as dt
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
# from .models import Candidate_registration, CandidateActivity, Candidate_Interview, Employee, VacancyDetails, Company_registration

# Import the necessary models from your application
# (Assuming Employee, VacancyDetails, and Company_registration are in the same app)

@login_required(login_url='/crm/404/')
def admin_candidate_profile(request, id):
    if request.user.is_staff or request.user.is_superuser:
        candidate = get_object_or_404(Candidate_registration.objects.prefetch_related('activities__employee', 'interviews'), id=id)
        logged_in_employee = Employee.objects.get(user=request.user)
        employees = Employee.objects.all().order_by('-id')
        vacancies = VacancyDetails.objects.filter(
            vacancy_status='Active'
        ).select_related('company').values(
            'id',
            'job_profile',
            'company__company_name'
        )
        companies = Company_registration.objects.all().order_by('-id')

        # Log admin view activity if the user is staff or superuser
    if request.user.is_staff or request.user.is_superuser:
        try:
            # This assumes your Employee model is linked to the User model
            # For example: employee = Employee.objects.get(user=request.user)
            employee_instance = request.user.employee 
        except Employee.DoesNotExist:
            employee_instance = None

        if employee_instance:
            # Avoid creating duplicate 'viewed' logs on every page refresh
            last_activity = candidate.activities.first()

            # Check if the last activity was within the last 5 seconds (to prevent logging after a redirect)
            is_recent_activity = last_activity and (timezone.now() - last_activity.timestamp < timedelta(seconds=5))

            # Only log a 'viewed' action if there hasn't been a very recent activity
            if not is_recent_activity:
                # (Put your existing logic for creating a 'viewed' activity log here)
                # For example:
                CandidateActivity.objects.create(
                    candidate=candidate,
                    employee=logged_in_employee,
                    action='viewed',
                    remark=f"Profile viewed by admin: {request.user.username}"
                )

        if request.method == 'POST':
            # Handle general candidate profile updates
            if 'submit_all' in request.POST:
                # Update fields from POST
                candidate.candidate_name = request.POST.get('candidate_name')
                candidate.candidate_mobile_number = request.POST.get('candidate_mobile_number')
                candidate.candidate_email_address = request.POST.get('candidate_email_address')
                candidate.gender = request.POST.get('gender')
                candidate.lead_source = request.POST.get('lead_source')
                candidate.employee_assigned = request.POST.get('employee_assigned')

                # Multi-selects
                candidate.preferred_location = ', '.join(request.POST.getlist('preferred_location'))
                candidate.preferred_state = ', '.join(request.POST.getlist('preferred_state'))
                candidate.origin_location = request.POST.get('origin_location')
                candidate.qualification = request.POST.get('qualification')
                candidate.diploma = request.POST.get('diploma')
                candidate.sector = ', '.join(request.POST.getlist('sector'))
                candidate.department = ', '.join(request.POST.getlist('department'))

                candidate.experience_year = request.POST.get('experience_year')
                candidate.experience_month = request.POST.get('experience_month')
                candidate.current_company = request.POST.get('current_company')
                candidate.current_working_status = request.POST.get('current_working_status')
                candidate.current_salary = request.POST.get('current_salary')
                candidate.current_salary_type = request.POST.get('current_salary_type')
                candidate.expected_salary = request.POST.get('expected_salary')
                candidate.expected_salary_type = request.POST.get('expected_salary_type')
                candidate.submit_by = request.POST.get('submit_by')

                candidate.call_connection = request.POST.get('call_connection')
                candidate.calling_remark = request.POST.get('calling_remark')
                candidate.lead_generate = request.POST.get('lead_generate')
                candidate.send_for_interview = request.POST.get('send_for_interview')
                candidate.next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None
                candidate.lead_for = request.POST.get('lead_for')

                candidate.selection_status = request.POST.get('selection_status')
                candidate.company_name = request.POST.get('company_name')
                candidate.job_title = request.POST.get('job_title')
                candidate.offered_salary = request.POST.get('offered_salary')
                candidate.selection_date = request.POST.get('selection_date') or None
                candidate.candidate_joining_date = request.POST.get('candidate_joining_date') or None
                candidate.emta_commission = request.POST.get('emta_commission')
                candidate.payout_date = request.POST.get('payout_date') or None
                candidate.joining_status = request.POST.get('joining_status')
                candidate.selection_remark = request.POST.get('selection_remark')
                candidate.expected_joining_date = request.POST.get('expected_joining_date') or None

                candidate.other_lead_source = request.POST.get('other_lead_source')
                candidate.other_qualification = request.POST.get('other_qualification')
                candidate.other_working_status = request.POST.get('other_working_status')
                candidate.other_call_connection = request.POST.get('other_call_connection')
                candidate.other_lead_generate = request.POST.get('other_lead_generate')
                candidate.other_interview_status = request.POST.get('other_interview_status')
                candidate.other_selection_status = request.POST.get('other_selection_status')
                candidate.other_origin_location = request.POST.get('other_origin_location')
                candidate.other_preferred_location = request.POST.get('other_preferred_location')
                candidate.other_sector = request.POST.get('other_sector')
                candidate.other_department = request.POST.get('other_department')

                candidate.admin_remark = request.POST.get('admin_remark')
                
                # Handle file uploads and clearing
                if 'candidate_photo' in request.FILES:
                    candidate.candidate_photo = request.FILES['candidate_photo']
                elif request.POST.get('candidate_photo-clear'):
                    candidate.candidate_photo = None

                if 'candidate_resume' in request.FILES:
                    candidate.candidate_resume = request.FILES['candidate_resume']
                elif request.POST.get('candidate_resume-clear'):
                    candidate.candidate_resume = None

                # Pass the logged_in_employee to the save method
                # The save method's logic will now handle logging the activity
                candidate.updated_by = logged_in_employee
                candidate.save(user=logged_in_employee)

                messages.success(request, 'Candidate details updated successfully!')
                return redirect('admin_candidate_profile', id=id)
            

            # Handle invoice related data
            elif 'invoice_releted_data' in request.POST:
                candidate.invoice_status = request.POST.get('invoice_status')
                candidate.invoice_date = request.POST.get('invoice_date') or None
                candidate.invoice_amount = request.POST.get('invoice_amount')
                candidate.invoice_remark = request.POST.get('invoice_remark')
                candidate.invoice_paid_status = request.POST.get('invoice_paid_status')
                candidate.invoice_number = request.POST.get('invoice_number')

                if 'invoice_attachment' in request.FILES:
                    candidate.invoice_attachment = request.FILES['invoice_attachment']
                elif request.POST.get('clear_invoice_attachment'): 
                    candidate.invoice_attachment = None

                candidate.updated_by = logged_in_employee
                candidate.save(user=logged_in_employee) # Pass user to model's save method
                messages.success(request, 'Invoice details updated successfully!')
                return redirect('admin_candidate_profile', id=id)

            # Handle adding a new interview
            elif 'add_interview_submit' in request.POST:
                try:
                    interview_date_time_str = request.POST.get('interview_date_time')
                    if interview_date_time_str:
                        interview_date_time = dt.datetime.strptime(interview_date_time_str, '%Y-%m-%dT%H:%M')
                    else:
                        interview_date_time = None

                    interview = Candidate_Interview.objects.create(
                        candidate=candidate,
                        interview_date_time=interview_date_time,
                        company_name=request.POST.get('interview_company_name'),
                        job_position=request.POST.get('job_position'),
                        interviewer_name=request.POST.get('interviewer_name'),
                        interviewer_email=request.POST.get('interviewer_email'),
                        interviewer_phone=request.POST.get('interviewer_phone'),
                        status=request.POST.get('status'),
                        interview_mode=request.POST.get('interview_mode'),
                        location=request.POST.get('location'),
                        meeting_link=request.POST.get('meeting_link'),
                        notes=request.POST.get('notes'),
                        feedback=request.POST.get('feedback'),
                        rating=request.POST.get('rating') or None,
                        is_technical=request.POST.get('is_technical') == 'on',
                        duration=request.POST.get('duration') or None,
                        requirements=request.POST.get('requirements'),
                        created_by=request.user, 
                        updated_by=request.user, 
                    )
                    if 'interview_attachment' in request.FILES:
                        interview.attachment = request.FILES['interview_attachment']
                        interview.save() # Save again to process the file upload

                    # Log the interview creation manually as it's a separate model
                    CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action='created',
                        remark=f"New interview added for {interview.company_name} on {interview.interview_date_time}"
                    )

                    messages.success(request, 'Interview added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding interview: {e}')
                return redirect('admin_candidate_profile', id=id)

            # Handle editing an existing interview
            elif 'edit_interview_submit' in request.POST:
                interview_id = request.POST.get('interview_id')
                interview = get_object_or_404(Candidate_Interview, id=interview_id, candidate=candidate)
                
                # Capture original data for logging before updating
                original_interview_data = {
                    field.name: getattr(interview, field.name) for field in interview._meta.fields
                }

                # Update fields with new values from POST
                interview_date_time_str = request.POST.get('interview_date_time')
                if interview_date_time_str:
                    interview.interview_date_time = dt.datetime.strptime(interview_date_time_str, '%Y-%m-%dT%H:%M')
                else:
                    interview.interview_date_time = None
                
                interview.company_name = request.POST.get('interview_company_name')
                interview.job_position = request.POST.get('job_position')
                interview.interviewer_name = request.POST.get('interviewer_name')
                interview.interviewer_email = request.POST.get('interviewer_email')
                interview.interviewer_phone = request.POST.get('interviewer_phone')
                interview.status = request.POST.get('status')
                interview.interview_mode = request.POST.get('interview_mode')
                interview.location = request.POST.get('location')
                interview.meeting_link = request.POST.get('meeting_link')
                interview.notes = request.POST.get('notes')
                interview.feedback = request.POST.get('feedback')
                interview.rating = request.POST.get('rating') or None
                interview.is_technical = request.POST.get('is_technical') == 'on'
                interview.duration = request.POST.get('duration') or None
                interview.requirements = request.POST.get('requirements')

                # Handle attachment file upload or clear checkbox
                if 'interview_attachment' in request.FILES:
                    interview.attachment = request.FILES['interview_attachment']
                elif request.POST.get('clear_interview_attachment') == 'on':
                    interview.attachment = None
                
                interview.updated_by = request.user
                interview.save() # Save the object first to process file changes

                # Build the changes dictionary for logging
                interview_changes = {}
                for field in interview._meta.fields:
                    field_name = field.name
                    old_value = original_interview_data[field_name]
                    new_value = getattr(interview, field_name)
                    
                    # Ensure values are comparable (e.g., strings)
                    if isinstance(old_value, (dt.date, dt.datetime, models.FileField)):
                        old_value = str(old_value)
                    if isinstance(new_value, (dt.date, dt.datetime, models.FileField)):
                        new_value = str(new_value)
                        
                    if old_value != new_value:
                        interview_changes[field_name] = {'old': old_value, 'new': new_value}

                if interview_changes:
                    CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action=f'Interview updated (ID: {interview.id})',
                        changes=interview_changes,
                        remark=f"Interview details updated by {logged_in_employee.user.username}"
                    )
                messages.success(request, 'Interview updated successfully!')
                return redirect('admin_candidate_profile', id=id)

            # Handle deleting an interview
            elif 'delete_interview_submit' in request.POST:
                interview_id = request.POST.get('interview_id')
                interview = get_object_or_404(Candidate_Interview, id=interview_id, candidate=candidate)
                
                # Capture details for logging before deletion
                interview_details_for_log = {
                    'company_name': interview.company_name,
                    'job_position': interview.job_position,
                    'interview_date_time': str(interview.interview_date_time) if interview.interview_date_time else None,
                    'attachment_name': interview.attachment.name if interview.attachment else None
                }
                
                interview.delete()
                
                # Log the deletion
                CandidateActivity.objects.create(
                    candidate=candidate,
                    employee=logged_in_employee,
                    action=f'Interview deleted',
                    changes={'deleted_interview': interview_details_for_log},
                    remark=f"Interview deleted by {logged_in_employee.user.username}"
                )
                messages.success(request, 'Interview deleted successfully!')
                return redirect('admin_candidate_profile', id=id)

            elif 'bfsi_releted_data' in request.POST:
                candidate.bfsi_batch_date = request.POST.get('bfsi_batch_date') or None
                candidate.bfsi_payment_status = request.POST.get('bfsi_payment_status')
                candidate.bfsi_payment_date = request.POST.get('bfsi_payment_date') or None
                candidate.bfsi_payment_remark = request.POST.get('bfsi_payment_remark')
                candidate.bfsi_payment_attachment = request.FILES.get('bfsi_payment_attachment')
                candidate.bfsi_candidature_status = request.POST.get('bfsi_candidature_status')
                candidate.save()
                messages.success(request, 'BFSI releted details updated successfully!')
                return redirect('admin_candidate_profile', id=id)

            # Redirect after any POST request that doesn't fall into the above
            return redirect('admin_candidate_profile', id=id)

        # GET request context
        state = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana",
                 "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                 "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
                 "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
                 "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
                 "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"]

        state_district = {
            "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"], 
            "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang"],
            "Assam": ["Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong"],
            "Bihar": ["Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
            "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur"],
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
            "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
            "Chandigarh": ["Chandigarh"],
            "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
            "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
            "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
            "Ladakh": ["Kargil", "Leh"],
            "Lakshadweep": ["Lakshadweep"],
            "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
        }

        districts = sorted(list(set(d for sublist in state_district.values() for d in sublist)))

        job_sectors = [
            "IT (Information Technology)", "BPO (Business Process Outsourcing)", "Banking and Finance",
            "Healthcare and Pharmaceuticals", "Education and Training",
            "Retail and E-commerce", "Manufacturing and Production", "Real Estate and Construction", "Hospitality and Tourism",
            "Media and Entertainment", "Telecommunications", "Logistics and Supply Chain", "Marketing and Advertising", "Human Resources",
            "Legal and Compliance", "Engineering and Infrastructure", "Automobile Industry",
            "Fashion and Textile", "FMCG (Fast Moving Consumer Goods)",
            "Agriculture and Farming", "Insurance", "Government Sector", "NGO and Social Services",
            "Energy and Power", "Aviation and Aerospace"
        ]
        departments = [
            "Software Development", "IT Support", "Web Development",
            "Network Administration", "Cybersecurity",
            "Data Science & Analytics", "Cloud Computing", "Quality Assurance (QA)",
            "Customer Support", "Technical Support", "Voice Process",
            "Non-Voice Process", "Back Office Operations",
            "Investment Banking", "Retail Banking", "Loan Processing",
            "Risk Management", "Accounting and Auditing",
            "Financial Analysis", "Wealth Management",
            "Medical Representatives", "Clinical Research", "Nursing",
            "Medical Technicians", "Pharmacy Operations",
            "Healthcare Administration",
            "Teaching", "Curriculum Development", "Academic Counseling",
            "E-Learning Development", "Education Administration",
            "Store Operations", "Supply Chain Management",
            "Sales and Merchandising", "E-commerce Operations", "Digital Marketing",
            "Production Planning", "Quality Control", "Maintenance and Repair",
            "Operations Management", "Inventory Management",
            "Sales and Marketing", "Civil Engineering", "Project Management",
            "Interior Designing", "Surveying and Valuation",
            "Hotel Management", "Travel Coordination", "Event Planning",
            "Food and Beverage Services", "Guest Relations",
            "Content Writing", "Video Editing", "Graphic Designing",
            "Social Media Management", "Event Production",
            "Network Installation", "Customer Support", "Telecom Engineering",
            "Technical Operations", "Business Development",
            "Logistics Coordination", "Warehouse Management", "Procurement",
            "Transportation Management", "Inventory Control",
            "Market Research", "Brand Management", "Advertising Sales",
            "Public Relations", "Digital Marketing",
            "Recruitment", "Employee Relations", "Payroll and Benefits",
            "Training and Development", "HR Analytics",
            "Corporate Law", "Compliance Auditing", "Contract Management",
            "Intellectual Property Rights", "Legal Advisory",
            "Civil Engineering", "Mechanical Engineering",
            "Electrical Engineering", "Project Planning", "Structural Design",
            "Automotive Design", "Production and Assembly", "Sales and Service",
            "Supply Chain Management", "Quality Assurance",
            "Fashion Design", "Merchandising", "Production Management",
            "Quality Control", "Retail Sales",
            "Sales and Marketing", "Supply Chain Operations",
            "Production Management", "Quality Control", "Brand Management",
            "Agribusiness Management", "Farm Operations", "Food Processing",
            "Agricultural Sales", "Quality Assurance",
            "Sales and Business Development", "Underwriting",
            "Claims Management", "Actuarial Services", "Policy Administration",
            "Administrative Services", "Public Relations",
            "Policy Analysis", "Clerical Positions", "Field Operations",
            "Community Development", "Fundraising", "Program Management",
            "Volunteer Coordination", "Policy Advocacy",
            "Renewable Energy Operations", "Power Plant Engineering",
            "Energy Efficiency Management", "Electrical Design", "Maintenance",
            "Aviation and Aerospace",
            "Flight Operations", "Ground Staff", "Aircraft Maintenance",
            "Cabin Crew", "Research and Development"
        ]

        context = {
            'candidate': candidate,
            'activities': candidate.activities.all().order_by('-timestamp'),
            'interviews': candidate.interviews.all().order_by('-interview_date_time'),
            'today': timezone.now().date(),
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
            'vacancies': vacancies,
            'companies': companies,
            'state': state,
            'state_district': state_district,
            'employees': employees,
            'interview_statuses': Candidate_Interview.INTERVIEW_STATUS,
            'interview_modes': Candidate_Interview.INTERVIEW_MODE,
        }
        return render(request, 'crm/candidate-profile.html', context)
    else:
        messages.error(request, "You are not authorized to view this page.")
        return render(request, 'crm/404.html', status=404)
    
from Employee.utils import extract_text_from_file, parse_resume_data # Import the utility created above

# --- 1. NEW VIEW FOR AJAX PARSING ---
@login_required
def parse_resume_view(request):
    if request.method == 'POST' and request.FILES.get('resume_file'):
        uploaded_file = request.FILES['resume_file']
        
        # Extract text
        text = extract_text_from_file(uploaded_file)
        
        if not text:
            return JsonResponse({'status': 'error', 'message': 'Could not read file text.'})
        
        # Parse data
        parsed_data = parse_resume_data(text)
        
        return JsonResponse({'status': 'success', 'data': parsed_data})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required(login_url='/crm/404/')
def admin_candidate_registration(request):
    logged_in_employee = Employee.objects.get(user=request.user)
    
    if request.method == 'POST':
        candidate_mobile_number = request.POST.get('candidate_mobile_number')
        
        # Check for duplicates by mobile number
        try:
            duplicate_candidate = Candidate_registration.objects.get(
                candidate_mobile_number=candidate_mobile_number
            )
            # If a duplicate is found, return a JSON response with the candidate's details
            return JsonResponse({
                'status': 'duplicate',
                'message': 'Mobile number already registered.',
                'candidate_id': duplicate_candidate.id,
                'candidate_name': duplicate_candidate.candidate_name,
                'candidate_profile_url': reverse('admin_candidate_profile', args=[duplicate_candidate.id])
            }, status=409)  # Use status code 409 for Conflict
        except Candidate_registration.DoesNotExist:
            pass # No duplicate found, continue with registration

        # Process the form data
        candidate_name = request.POST.get('candidate_name')
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
        next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None
        remark = request.POST.get('remark')
        submit_by = request.POST.get('submit_by')
        preferred_location_str = ', '.join(preferred_location)
        sector_str = ', '.join(sector)
        department_str = ', '.join(department)
        other_lead_source = request.POST.get('other_lead_source')
        other_qualification = request.POST.get('other_qualification')
        other_origin_location = request.POST.get('other_origin_location')
        other_preferred_location = request.POST.get('other_preferred_location')
        other_sector = request.POST.get('other_sector')
        other_department = request.POST.get('other_department')
        current_salary_type = request.POST.get('current_salary_type')
        expected_salary_type = request.POST.get('expected_salary_type')

        # --- RENAME RESUME LOGIC STARTS ---
        if candidate_resume and candidate_name:
            # Get file extension (e.g., .pdf)
            ext = os.path.splitext(candidate_resume.name)[1]
            # Create new name: Name_Resume.pdf (Sanitize name to remove spaces/special chars)
            clean_name = "".join(x for x in candidate_name if x.isalnum())
            new_filename = f"{clean_name}_Resume{ext}"
            candidate_resume.name = new_filename
        # --- RENAME RESUME LOGIC ENDS ---
        
        # Save to database
        candidate = Candidate_registration.objects.create(
            employee_name=logged_in_employee,
            candidate_name=candidate_name,
            candidate_mobile_number=candidate_mobile_number,
            candidate_alternate_mobile_number=candidate_alternate_mobile_number,
            candidate_email_address=candidate_email_address,
            gender=gender,
            lead_source=lead_source,
            preferred_location=preferred_location_str,
            origin_location=origin_location,
            qualification=qualification,
            diploma=diploma,
            sector=sector_str,
            department=department_str,
            experience_year=experience_year,
            experience_month=experience_month,
            current_company=current_company,
            current_working_status=current_working_status,
            current_salary=current_salary,
            expected_salary=expected_salary,
            call_connection=call_connection,
            calling_remark=calling_remark,
            lead_generate=lead_generate,
            send_for_interview=send_for_interview,
            next_follow_up_date_time=next_follow_up_date_time,
            candidate_photo=candidate_photo,
            candidate_resume=candidate_resume,
            remark=remark,
            submit_by=submit_by,
            other_lead_source=other_lead_source,
            other_qualification=other_qualification,
            other_origin_location=other_origin_location,
            other_preferred_location=other_preferred_location,
            other_sector=other_sector,
            other_department=other_department,
            current_salary_type=current_salary_type,
            expected_salary_type=expected_salary_type
        )

        # Create a CandidateActivity record
        CandidateActivity.objects.create(
            candidate=candidate,
            employee=logged_in_employee,
            action='created',
            # changes=changes,
            remark="Created via unified form"
        )

        return JsonResponse({'status': 'success', 'redirect_url': reverse('admin_candidate_list')})
    else:
        # suggested_unique_code = get_next_unique_code()

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
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"

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
            # 'suggested_unique_code':suggested_unique_code,
            'districts' : districts,
            'job_sectors' : job_sectors,
            'departments' : departments,
            'state' : state,
            'state_distict' : state_distict
        }
        return render (request,'crm/candidate-registration.html',context)
   

@login_required(login_url='/employee/404/')
@require_POST
def check_mobile_number_duplicate(request):
    """
    Checks if a mobile number already exists and returns details for the modal.
    """
    try:
        data = json.loads(request.body)
        mobile_number = data.get('mobile_number')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    if mobile_number:
        try:
            duplicate_candidate = Candidate_registration.objects.get(
                candidate_mobile_number=mobile_number
            )
            # If a candidate is found, return all data needed for the modal
            return JsonResponse({
                'status': 'duplicate',
                'candidate_name': duplicate_candidate.candidate_name,
                # ADD THIS LINE to provide the URL for the button
                'candidate_profile_url': reverse('admin_candidate_profile', args=[duplicate_candidate.id])
            }, status=409)
        except Candidate_registration.DoesNotExist:
            # If no candidate is found, return a success status
            return JsonResponse({'status': 'unique'}, status=200)

    return JsonResponse({'error': 'Mobile number is required'}, status=400)

@login_required(login_url='/crm/404/')
def admin_candidate_bulk_upload(request):
    if request.user.is_staff or request.user.is_superuser:
        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"

        ]
        
        
        if request.method == 'POST':
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                messages.error(request, 'Please select an Excel file to upload.')
                return redirect('admin_candidate_bulk_upload')
            
            try:
                # Read the Excel file
                if excel_file.name.endswith('.xlsx'):
                    df = pd.read_excel(excel_file, engine='openpyxl')
                elif excel_file.name.endswith('.xls'):
                    df = pd.read_excel(excel_file)
                else:
                    messages.error(request, 'Invalid file format. Please upload an Excel file (.xlsx or .xls).')
                    return redirect('admin_candidate_bulk_upload')
                
                # Validate required columns - only candidate_name and mobile_number are mandatory
                required_columns = ['candidate_name', 'candidate_mobile_number']
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                    return redirect('admin_candidate_bulk_upload')
                
                success_count = 0
                duplicate_count = 0
                error_messages = []
                
                for index, row in df.iterrows():
                    try:
                        # Skip if candidate_name or mobile_number is empty
                        if pd.isna(row['candidate_name']) or pd.isna(row['candidate_mobile_number']):
                            error_messages.append(f"Row {index + 2}: Missing candidate name or mobile number")
                            continue
                        
                        # Clean and validate mobile number
                        mobile_number = str(row['candidate_mobile_number']).strip()
                        if not mobile_number:
                            error_messages.append(f"Row {index + 2}: Mobile number cannot be empty")
                            continue
                        
                        # Check if candidate already exists by mobile number
                        if Candidate_registration.objects.filter(candidate_mobile_number=mobile_number).exists():
                            duplicate_count += 1
                            continue  # Skip duplicate candidates
                        
                        # Process each row
                        preferred_location = row.get('preferred_location', '')
                        if isinstance(preferred_location, str):
                            preferred_location = [loc.strip() for loc in preferred_location.split(',') if loc.strip()]
                        
                        sector = row.get('sector', '')
                        if isinstance(sector, str):
                            sector = [s.strip() for s in sector.split(',') if s.strip()]
                        
                        department = row.get('department', '')
                        if isinstance(department, str):
                            department = [d.strip() for d in department.split(',') if d.strip()]
                        
                       
                        # Get employee name from Excel or use empty string
                        employee_name = row.get('employee_name', '')
                        
                        # Create candidate
                        candidate = Candidate_registration(
                            employee_name=row.get('employee_name', ''),
                            candidate_name=row['candidate_name'].strip(),
                            # unique_code=row.get('unique_code', admin_get_next_unique_code(request)),
                            candidate_mobile_number=mobile_number,
                            candidate_alternate_mobile_number=str(row.get('candidate_alternate_mobile_number', '')).strip(),
                            candidate_email_address=str(row.get('candidate_email_address', '')).strip(),
                            gender=row.get('gender', ''),
                            lead_source=row.get('lead_source', ''),
                            preferred_location=', '.join(preferred_location) if preferred_location else '',
                            origin_location=row.get('origin_location', ''),
                            qualification=row.get('qualification', ''),
                            diploma=row.get('diploma', ''),
                            sector=', '.join(sector) if sector else '',
                            department=', '.join(department) if department else '',
                            experience_year=row.get('experience_year', 0),
                            experience_month=row.get('experience_month', 0),
                            current_company=row.get('current_company', ''),
                            current_working_status=row.get('current_working_status', ''),
                            current_salary=row.get('current_salary', 0),
                            expected_salary=row.get('expected_salary', 0),
                            call_connection=row.get('call_connection', 'No'),
                            calling_remark=row.get('calling_remark', ''),
                            lead_generate=row.get('lead_generate', 'No'),
                            send_for_interview=row.get('send_for_interview', 'No'),
                            remark=row.get('remark', ''),
                        )
                        
                        # Save the candidate
                        candidate.save()
                        success_count += 1
                        
                    except Exception as e:
                        error_messages.append(f"Row {index + 2}: {str(e)}")
                        continue
                
                # Prepare result message
                if success_count > 0:
                    messages.success(request, f'Successfully imported {success_count} candidates.')
                if duplicate_count > 0:
                    messages.warning(request, f'Skipped {duplicate_count} duplicate candidates (existing mobile number).')
                if error_messages:
                    messages.error(request, f'Errors in {len(error_messages)} rows. See details below.')
                    for error in error_messages[:5]:  # Show first 5 errors to avoid flooding
                        messages.error(request, error)
                    if len(error_messages) > 5:
                        messages.info(request, f'... and {len(error_messages)-5} more errors.')
                
                return redirect('admin_candidate_bulk_upload')
            
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                return redirect('admin_candidate_bulk_upload')
        
        # Prepare context for GET request
        context = {
            'districts': districts,
            'template_url': '/static/candidate_bulk_upload_template.xlsx'
        }
        return render(request, 'crm/candidate-bulk-upload.html', context)
    
    else:
        return render(request, 'crm/404.html', status=404)
    
# crm/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# from .models import Candidate_registration, Candidate
from itertools import chain
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils.text import slugify

# Helper to get unique, sorted, non-empty values from multiple models for a given field
def get_unique_filter_options(*querysets, field_name):
    values = set()
    for qs in querysets:
        values.update(qs.values_list(field_name, flat=True).distinct())
    # Filter out None or empty strings and sort
    return sorted([v for v in values if v])

@login_required(login_url='/crm/404/')
def admin_candidate_list(request):
    """
    Renders the main candidate list page. It now includes a list of all employees
    for the new bulk assignment modal.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    candidates_reg_qs = Candidate_registration.objects.all()
    candidates_can_qs = Candidate.objects.all()

    # --- Fetch all possible filter options for the dropdowns ---
    filter_options = {
        'connection_statuses': get_unique_filter_options(candidates_reg_qs, candidates_can_qs, field_name='call_connection'),
        'lead_sources': get_unique_filter_options(candidates_reg_qs, candidates_can_qs, field_name='lead_source'),
        'employees': get_unique_filter_options(candidates_reg_qs, candidates_can_qs, field_name='employee_name'),
        'lead_statuses': get_unique_filter_options(candidates_reg_qs, candidates_can_qs, field_name='lead_generate'),
    }

    all_candidates_list = sorted(
        list(chain(candidates_reg_qs, candidates_can_qs)),
        key=lambda x: x.register_time,
        reverse=True
    )
    
    paginator = Paginator(all_candidates_list, 20)
    total_candidates_count = paginator.count
    candidates_page = paginator.page(1)

    for candidate in candidates_page.object_list:
        if isinstance(candidate, Candidate_registration):
            candidate.model_type = 'registration'
        else:
            candidate.model_type = 'candidate'

    # --- NEW: Fetch all employees for the assignment modal ---
    all_employees = Employee.objects.all().order_by('first_name', 'last_name', 'employee_id')
    employees = Employee.objects.all().order_by('first_name', 'last_name', 'employee_id')

    context = {
        'candidates': candidates_page.object_list,
        'total_candidates_count': total_candidates_count,
        'filter_options': filter_options,
        'all_employees': all_employees, # Pass employees to the template
        'employees' : employees,

    }
    return render(request, 'crm/candidate-list.html', context)

# your_app/views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.text import slugify
from itertools import chain

@login_required(login_url='/crm/404/')
def get_candidates_api(request):
    """
    API view to handle AJAX requests for fetching, filtering, and paginating candidates.
    This version is modified to include the latest admin activity for each candidate.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    # --- Queryset Optimization ---
    # Use prefetch_related to efficiently load activities and related user data in one go.
    # This is crucial for good performance.
    candidates_reg_qs = Candidate_registration.objects.prefetch_related(
        'activities__employee__user'
    ).all()
    
    # Assuming the `Candidate` model does not have an 'activities' relationship
    candidates_can_qs = Candidate.objects.all()

    # --- Filtering Logic (remains the same) ---
    search_term = request.GET.get('search', '').strip()
    date_from = request.GET.get('dateFrom')
    date_to = request.GET.get('dateTo')
    connection_statuses = [s for s in request.GET.get('connectionStatus', '').split(',') if s]
    lead_sources = [s for s in request.GET.get('leadSource', '').split(',') if s]
    employees = [s for s in request.GET.get('employee', '').split(',') if s]
    lead_statuses = [s for s in request.GET.get('status', '').split(',') if s]

    q_filter = Q()
    if search_term:
        q_filter &= (Q(candidate_name__icontains=search_term) | Q(candidate_mobile_number__icontains=search_term) | Q(unique_code__icontains=search_term) | Q(current_working_status__icontains=search_term))
    if date_from:
        q_filter &= Q(register_time__date__gte=date_from)
    if date_to:
        q_filter &= Q(register_time__date__lte=date_to)
    if connection_statuses:
        q_filter &= Q(call_connection__in=connection_statuses)
    if lead_sources:
        q_filter &= Q(lead_source__in=lead_sources)
    if employees:
        q_filter &= Q(employee_name__in=employees)
    if lead_statuses:
        q_filter &= Q(lead_generate__in=lead_statuses)
    
    candidates_reg_qs = candidates_reg_qs.filter(q_filter)
    candidates_can_qs = candidates_can_qs.filter(q_filter)

    # --- Sorting and Pagination (remains the same) ---
    filtered_candidates_list = sorted(
        list(chain(candidates_reg_qs, candidates_can_qs)),
        key=lambda x: x.register_time,
        reverse=True
    )
    
    paginator = Paginator(filtered_candidates_list, 20)
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        return JsonResponse({'candidates': [], 'has_next': False, 'total_count': 0})

    # --- Data Serialization ---
    candidates_data = []
    for candidate in page_obj.object_list:
        model_type = 'registration' if isinstance(candidate, Candidate_registration) else 'candidate'
        
        # ▼▼▼ NEW: Logic to find the latest admin activity ▼▼▼
        latest_admin_activity = None
        # Only Candidate_registration objects have activities based on your models
        if model_type == 'registration':
            # Because of prefetch_related, this does NOT cause extra database queries.
            # The list is already ordered by timestamp descending from the model's Meta.
            activity_list = candidate.activities.all()
            if activity_list:
                latest_activity = activity_list[0]
                # Check if the activity was performed by a staff/admin user
                if latest_activity.employee and latest_activity.employee.user and latest_activity.employee.user.is_staff:
                    latest_admin_activity = {
                        'action': latest_activity.action,
                        'admin_username': latest_activity.employee.user.username,
                        'timestamp': latest_activity.timestamp.strftime('%b %d, %Y')
                    }
        # ▲▲▲ END of new logic ▲▲▲

        profile_url = reverse('admin_candidate_profile', args=[candidate.id])
        if candidate.lead_source == 'EVMS':
            profile_url = reverse('evms_candidate_profile', args=[candidate.id])

        candidates_data.append({
            'id': candidate.id,
            'model_type': model_type,
            'call_connection': candidate.call_connection,
            'photo_url': candidate.candidate_photo.url if candidate.candidate_photo else None,
            'name': candidate.candidate_name,
            'name_initial': candidate.candidate_name[0].upper() if candidate.candidate_name else '',
            'unique_code': candidate.unique_code,
            'refer_code': getattr(candidate, 'refer_code', ''),
            'unique_id': getattr(candidate, 'unique_id', ''),
            'mobile': candidate.candidate_mobile_number,
            'email': candidate.candidate_email_address,
            'lead_source': candidate.lead_source,
            'other_lead_source': getattr(candidate, 'other_lead_source', ''),
            'lead_status': candidate.lead_generate,
            'other_lead_status': getattr(candidate, 'other_lead_generate', ''),
            'experience_year': candidate.experience_year,
            'experience_month': candidate.experience_month,
            'employee_name': candidate.employee_name,
            'registered_time': candidate.register_time.strftime("%b %d, %Y %H:%M"),
            'full_registered_time': candidate.register_time.isoformat(),
            'resume_url': candidate.candidate_resume.url if candidate.candidate_resume else None,
            'profile_url': profile_url,
            'data_status': slugify(candidate.lead_generate or ''),
            'data_connection_status': slugify(candidate.call_connection or 'unknown'),
            'data_lead_source': slugify(candidate.lead_source or 'unknown'),
            'data_employee_name': slugify(candidate.employee_name or 'unassigned'),
            'latest_admin_activity': latest_admin_activity,  # Add the new data to the response
        })
        
    return JsonResponse({
        'candidates': candidates_data,
        'has_next': page_obj.has_next(),
        'total_count': paginator.count
    })


# --- NEW VIEW FOR BULK ASSIGNMENT ---
@login_required(login_url='/crm/404/')
@require_POST
def bulk_assign_candidates_api(request):
    """
    API endpoint to handle the bulk assignment of candidates to an employee.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

    try:
        data = json.loads(request.body)
        candidates_to_assign = data.get('candidates', [])
        employee_id = data.get('employee_id')

        if not candidates_to_assign or not employee_id:
            return JsonResponse({'status': 'error', 'message': 'Missing candidate or employee information.'}, status=400)

        employee_instance = Employee.objects.get(pk=employee_id)
        
        # Separate candidates by their model type
        reg_ids = [c['id'] for c in candidates_to_assign if c['model_type'] == 'registration']
        can_ids = [c['id'] for c in candidates_to_assign if c['model_type'] == 'candidate']

        updated_reg_count = 0
        updated_can_count = 0

        # Update both the new `assigned_to` ForeignKey and the old `employee_name` CharField
        employee_full_name = f"{employee_instance.first_name} {employee_instance.last_name} ({employee_instance.employee_id})"

        if reg_ids:
            updated_reg_count = Candidate_registration.objects.filter(pk__in=reg_ids).update(
                assigned_to=employee_instance,
                employee_name=employee_full_name 
            )
        
        if can_ids:
            updated_can_count = Candidate.objects.filter(pk__in=can_ids).update(
                assigned_to=employee_instance,
                employee_name=employee_full_name
            )

        total_updated = updated_reg_count + updated_can_count
        return JsonResponse({
            'status': 'success',
            'message': f'{total_updated} candidates have been successfully assigned to {employee_full_name}.'
        })

    except Employee.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Selected employee not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required(login_url='/crm/404/')
def delete_candidate(request, candidate_id, model_type=None):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    try:
        candidate = None
        candidate_type = None
        
        # If model_type is provided, check only that specific model
        if model_type == 'registration':
            try:
                candidate = Candidate_registration.objects.get(id=candidate_id)
                candidate_type = 'registration'
            except Candidate_registration.DoesNotExist:
                pass
        elif model_type == 'candidate':
            try:
                candidate = Candidate.objects.get(id=candidate_id)
                candidate_type = 'candidate'
            except Candidate.DoesNotExist:
                pass
        else:
            # Fallback: try both models if no model_type specified
            try:
                candidate = Candidate_registration.objects.get(id=candidate_id)
                candidate_type = 'registration'
            except Candidate_registration.DoesNotExist:
                try:
                    candidate = Candidate.objects.get(id=candidate_id)
                    candidate_type = 'candidate'
                except Candidate.DoesNotExist:
                    pass
        
        if candidate:
            # Store candidate info for success message
            candidate_name = candidate.candidate_name
            candidate_mobile = candidate.candidate_mobile_number
            
            # Delete the candidate
            candidate.delete()
            
            messages.success(request, f'Candidate "{candidate_name}" ({candidate_mobile}) has been deleted successfully from {candidate_type} model.')
        else:
            messages.error(request, f'Candidate with ID {candidate_id} not found in {model_type if model_type else "either"} model.')
            
    except Exception as e:
        messages.error(request, f'Error deleting candidate: {str(e)}')
    
    return redirect('admin_candidate_list')
    
@login_required(login_url='/crm/404/')   
def admin_company_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        companys = Company_registration.objects.all().order_by('-id')
        return render(request,'crm/company-list.html',{'companys':companys})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_company_profile(request, id):
    if request.user.is_staff or request.user.is_superuser:
        company = get_object_or_404(Company_registration, id=id)
        
        if request.method == 'POST':
            # Handle Company Personal Information Form
            if 'company_personal_information' in request.POST:
                form_name = "Company Personal Information"
                old_values = {
                    'handled_by': company.handled_by,
                    'company_name': company.company_name,
                    'company_location': company.company_location,
                    'company_unique_code': company.company_unique_code,
                    'company_email_address': company.company_email_address,
                    'opened_by': company.opened_by,
                }
                
                company.handled_by = request.POST.get('handled_by')
                company.company_name = request.POST.get('company_name')
                company.company_location = request.POST.get('company_location')
                company.company_unique_code = request.POST.get('company_unique_code')
                company.company_email_address = request.POST.get('company_email_address')
                company.opened_by = request.POST.get('opened_by')
                company.pan_number = request.POST.get('pan_number')
                company.gst_number = request.POST.get('gst_number')
                company.state_code = request.POST.get('state_code')
                company.company_address = request.POST.get('company_address')
                company.updated_by = request.user
                
                if 'company_logo' in request.FILES:
                    old_values['company_logo'] = str(company.company_logo)
                    company.company_logo = request.FILES['company_logo']
                
                company.save(user=request.user, form_name=form_name)
                messages.success(request, 'Company details updated successfully!')

            # Handle Company Contact Details Form
            elif 'company_details' in request.POST:
                form_name = "Company Contact Details"
                old_values = {
                    'company_contact_person_name': company.company_contact_person_name,
                    'company_contact_person_contact_details': company.company_contact_person_contact_details,
                    'company_contact_person_designation': company.company_contact_person_designation,
                    'interview_address': company.interview_address,
                }
                
                company.company_contact_person_name = request.POST.get('company_contact_person_name')
                company.company_contact_person_contact_details = request.POST.get('company_contact_person_contact_details')
                company.company_contact_person_designation = request.POST.get('company_contact_person_designation')
                company.interview_address = request.POST.get('interview_address')
                company.updated_by = request.user
                
                company.save(user=request.user, form_name=form_name)
                messages.success(request, 'Company contact details updated successfully!')
                
            # Handle Proposal Status Form
            elif 'submit_calling_remark' in request.POST:
                form_name = "Company Proposal Status"
                old_values = {
                    'status_of_proposal': company.status_of_proposal,
                    'invoice_generation_date': company.invoice_generation_date,
                    'payout_date': company.payout_date,
                    'payment_condiation': company.payment_condiation,
                    'remark': company.remark,
                }
                
                company.status_of_proposal = request.POST.get('status_of_proposal')
                company.invoice_generation_date = request.POST.get('invoice_generation_date') or None
                company.payout_date = request.POST.get('payout_date') or None
                company.payment_condiation = request.POST.get('payment_condiation')
                company.remark = request.POST.get('remark')
                company.updated_by = request.user
                
                company.save(user=request.user, form_name=form_name)
                messages.success(request, 'Company proposal details updated successfully!')
                
            # Handle New Vacancy Creation
            elif 'add_vacancy' in request.POST:
                form_name = "Add Vacancy"
                try:
                    vacancy = VacancyDetails(
                        company=company,
                        job_profile=request.POST.get('job_profile'),
                        company_vacancy_unique_code=request.POST.get('company_vacancy_unique_code'),
                        vacancy_opening_date=request.POST.get('vacancy_opening_date') or None,
                        vacancy_status=request.POST.get('vacancy_status', 'Pending'),
                        payroll=request.POST.get('payroll'),
                        third_party_name=request.POST.get('third_party_name'),
                        job_opening_origin=request.POST.get('job_opening_origin'),
                        sector_type=request.POST.get('sector_type'),
                        department_name=request.POST.get('department_name'),
                        fresher_status=request.POST.get('fresher_status'),
                        minimum_age=request.POST.get('minimum_age'),
                        maximum_age=request.POST.get('maximum_age'),
                        gender=request.POST.get('gender'),
                        minimum_experience=request.POST.get('minimum_experience'),
                        maximum_experience=request.POST.get('maximum_experience'),
                        minimum_education_qualification=request.POST.get('minimum_education_qualification'),
                        specialization=request.POST.get('specialization'),
                        minimum_salary_range=request.POST.get('minimum_salary_range'),
                        maximum_salary_range=request.POST.get('maximum_salary_range'),
                        vacancy_closing_date=request.POST.get('vacancy_closing_date') or None,
                        special_instruction=request.POST.get('special_instruction'),
                        company_usp=request.POST.get('company_usp'),
                        status_of_incentive=request.POST.get('status_of_incentive'),
                        replacement_criteria_days=request.POST.get('replacement_criteria_days'),
                        replacement_criteria=request.POST.get('replacement_criteria'),
                        payment_mode=request.POST.get('payment_mode'),
                        company_pay_type=request.POST.get('company_pay_type'),
                        flat_amount=request.POST.get('flat_amount'),
                        percentage_of_ctc=request.POST.get('percentage_of_ctc'),
                        pay_per_days=request.POST.get('pay_per_days'),
                        salary_transfer_date=request.POST.get('salary_transfer_date') or None,
                        expected_payment_date=request.POST.get('expected_payment_date') or None,
                        candidate_salary_transfer_date=request.POST.get('candidate_salary_transfer_date') or None,
                        created_by=request.user,
                        job_opening_origin_other = request.POST.get('job_opening_origin_other'),
                        interview_rounds = request.POST.get('interview_rounds'),
                        working_shift = request.POST.get('working_shift'),
                        working_shift_other = request.POST.get('working_shift_other'),
                        cab_facility = request.POST.get('cab_facility'),
                        cab_facility_other = request.POST.get('cab_facility_other'),
                        no_of_vacancies = request.POST.get('no_of_vacancies'),
                        batch_date = request.POST.get('batch_date'),
                        lingual_proficiency = request.POST.get('lingual_proficiency'),
                        incentive_details = request.POST.get('incentive_details'),
                        minimum_salary_type = request.POST.get('minimum_salary_type'),
                        maximum_salary_type = request.POST.get('maximum_salary_type'),
                        process_name = request.POST.get('process_name'),
                        job_profile_type = request.POST.get('job_profile_type'),
                        job_position = request.POST.get('job_position'),
                        job_description_attachment = request.FILES.get('job_description_attachment'),
                        experience_type = request.POST.get('experience_type'),
                        no_of_workingdays = request.POST.get('no_of_workingdays'),
                        shift_timing = request.POST.get('shift_timing'),
                        lingual_proficiency_specialization = request.POST.get('lingual_proficiency_specialization'),
                        times_of_interview = request.POST.get('times_of_interview')
                    )
                    vacancy.save(user=request.user, form_name=form_name)
                    messages.success(request, 'Vacancy added successfully!')
                except Exception as e:
                    messages.error(request, f'Error creating vacancy: {str(e)}')

            # Handle Vacancy Editing
            elif 'edit_vacancy' in request.POST:
                form_name = "Edit Vacancy"
                vacancy_id = request.POST.get('vacancy_id')
                try:
                    vacancy = VacancyDetails.objects.get(id=vacancy_id, company=company)
                    
                    # Store old values for tracking
                    old_values = {field.name: getattr(vacancy, field.name) 
                                for field in VacancyDetails._meta.fields 
                                if field.name not in ['id', 'created_at', 'updated_at']}
                    
                    # Update fields
                    vacancy.job_profile = request.POST.get('job_profile')
                    vacancy.company_vacancy_unique_code = request.POST.get('company_vacancy_unique_code')
                    vacancy.vacancy_opening_date = request.POST.get('vacancy_opening_date') or None
                    vacancy.vacancy_status = request.POST.get('vacancy_status', 'Pending')
                    vacancy.payroll = request.POST.get('payroll', '')
                    vacancy.third_party_name = request.POST.get('third_party_name', '')
                    vacancy.job_opening_origin = request.POST.get('job_opening_origin', '')
                    vacancy.sector_type = request.POST.get('sector_type', '')
                    vacancy.department_name = request.POST.get('department_name', '')
                    vacancy.fresher_status = request.POST.get('fresher_status', '')
                    vacancy.minimum_age = request.POST.get('minimum_age', '')
                    vacancy.maximum_age = request.POST.get('maximum_age', '')
                    vacancy.gender = request.POST.get('gender', '')
                    vacancy.minimum_experience = request.POST.get('minimum_experience', '')
                    vacancy.maximum_experience = request.POST.get('maximum_experience', '')
                    vacancy.minimum_education_qualification = request.POST.get('minimum_education_qualification', '')
                    vacancy.specialization = request.POST.get('specialization', '')
                    vacancy.minimum_salary_range = request.POST.get('minimum_salary_range', '')
                    vacancy.maximum_salary_range = request.POST.get('maximum_salary_range', '')
                    vacancy.vacancy_closing_date = request.POST.get('vacancy_closing_date') or None
                    vacancy.special_instruction = request.POST.get('special_instruction', '')
                    vacancy.company_usp = request.POST.get('company_usp', '')
                    vacancy.status_of_incentive = request.POST.get('status_of_incentive', '')
                    vacancy.replacement_criteria_days = request.POST.get('replacement_criteria_days', '')
                    vacancy.replacement_criteria = request.POST.get('replacement_criteria', '')
                    vacancy.process_name = request.POST.get('process_name', '')
                    vacancy.job_profile_type = request.POST.get('job_profile_type', '')
                    vacancy.job_position = request.POST.get('job_position', '')
                    vacancy.job_description_attachment = request.FILES.get('job_description_attachment', None)
                    vacancy.experience_type = request.POST.get('experience_type', '')
                    vacancy.no_of_workingdays = request.POST.get('no_of_workingdays', '')
                    vacancy.shift_timing = request.POST.get('shift_timing', '')
                    vacancy.lingual_proficiency_specialization = request.POST.get('lingual_proficiency_specialization', '')
                    vacancy.times_of_interview = request.POST.get('times_of_interview', '')

                    # Payment fields
                    vacancy.payment_mode = request.POST.get('payment_mode', '')
                    vacancy.company_pay_type = request.POST.get('company_pay_type', '')
                    keys = request.POST.getlist('flat_amount_key')
                    values = request.POST.getlist('flat_amount_value')

                    # Convert to JSON string for storing in CharField
                    vacancy.flat_amount = request.POST.get('flat_amount'),

                    try:
                        vacancy.percentage_of_ctc = float(request.POST.get('percentage_of_ctc', '')) if request.POST.get('percentage_of_ctc', '') else None
                        vacancy.pay_per_days = int(request.POST.get('pay_per_days', '')) if request.POST.get('pay_per_days', '') else None
                    except ValueError:
                        pass

                    vacancy.salary_transfer_date = request.POST.get('salary_transfer_date', '') or None
                    vacancy.expected_payment_date = request.POST.get('expected_payment_date', '') or None
                    vacancy.candidate_salary_transfer_date = request.POST.get('candidate_salary_transfer_date') or None
                    
                    vacancy.save(user=request.user, form_name=form_name)
                    messages.success(request, 'Vacancy updated successfully!')
                except VacancyDetails.DoesNotExist:
                    messages.error(request, 'Vacancy not found!')
                except Exception as e:
                    messages.error(request, f'Error updating vacancy: {str(e)}')
                   
            # Handle Vacancy Deletion
            elif 'delete_vacancy' in request.POST:
                vacancy_id = request.POST.get('vacancy_id')
                try:
                    vacancy = VacancyDetails.objects.get(id=vacancy_id, company=company)
                    job_title = vacancy.job_profile
                    company_name = vacancy.company.company_name
                    vacancy.delete()
                    
                    # Log deletion activity
                    CompanyActivity.objects.create(
                        content_type='vacancy',
                        employee=request.user,
                        action='status_changed',
                        changes={
                            'deleted': {
                                'old': f"{job_title} at {company_name}",
                                'new': "Deleted"
                            }
                        },
                        form_used="Delete Vacancy",
                        remark=f"Deleted vacancy: {job_title}"
                    )
                    
                    messages.success(request, 'Vacancy deleted successfully!')
                except VacancyDetails.DoesNotExist:
                    messages.error(request, 'Vacancy not found!')
                except Exception as e:
                    messages.error(request, f'Error deleting vacancy: {str(e)}')
                    
            return redirect('admin_company_profile', id=id)

        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"

        ]
        

        state = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", 
        "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        # Union Territories
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", 
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
        ]

        state_district = {
            "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"],  
            "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang"],
            "Assam": ["Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong"],
            "Bihar": ["Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
            "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur", "Narayanpur"],
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


        # Get all vacancies for the company
        vacancies = VacancyDetails.objects.filter(company=company).order_by('-created_at')
        
        # Get all activities - both company and vacancy activities
        company_activities = company.activities.all()
        vacancy_activities = CompanyActivity.objects.filter(vacancy__company=company)
        
        # Combine and sort activities by timestamp (newest first)
        all_activities = sorted(
            chain(
                company_activities.select_related('employee__employee'),
                vacancy_activities.select_related('employee__employee')
            ),
            key=lambda x: x.timestamp,
            reverse=True
        )[:20]
        
        employees = Employee.objects.all()
        context = {
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
            'company': company,
            'vacancies': vacancies,
            'activities': all_activities,
            'now': timezone.now(),
            'employees': employees,
            'state': state,
            'state_district': state_district,
        }

        return render(request, 'crm/company-profile.html', context)
    else:
        return render(request, 'crm/404.html', status=404)
    
    
@login_required(login_url='/crm/404/')
def admin_vendor_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        vendors = Vendor.objects.all().order_by('-id')
        return render(request,'crm/admin-vendor-list.html',{'vendors':vendors})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_evms_candidate_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        candidates = Candidate.objects.all().order_by('-id')
        return render(request,'crm/admin-evms-candidate-list.html',{'candidates':candidates})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_vendor_candidate_list(request, id):
    if request.user.is_staff or request.user.is_superuser:
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
                    return redirect('admin_vendor_candidate_list', id=employee.id)  # Redirect back to the same page

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
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"
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
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime as dt # Import datetime for date/time handling
from django.db.models.fields.files import FieldFile # Import FieldFile


@login_required(login_url='/crm/404/')
def evms_candidate_profile(request, id):
    if request.user.is_staff or request.user.is_superuser:
        candidate = get_object_or_404(Candidate, id=id)
        
        # Ensure logged_in_employee is retrieved for activity logging
        try:
            logged_in_employee = Employee.objects.get(user=request.user)
        except Employee.DoesNotExist:
            messages.error(request, "Employee profile not found for the logged-in user.")
            return render(request, 'crm/404.html', status=404)

        employees = Employee.objects.all()
        companies = Company_registration.objects.all()
        vacancies = VacancyDetails.objects.filter(
            vacancy_status='Active'
        ).select_related('company').values(
            'id',
            'job_profile',
            'company__company_name'
        )

        if request.method == 'POST':
            # Handle general candidate profile updates
            if 'submit_all' in request.POST:
                original_candidate = Candidate.objects.get(id=id) # Re-fetch to get original state for comparison
                changes = {}

                fields_to_track = [
                    'candidate_name', 'candidate_mobile_number', 'candidate_email_address',
                    'gender', 'lead_source',
                    'candidate_alternate_mobile_number', 'preferred_location', 'origin_location',
                    'qualification', 'diploma', 'sector', 'department', 'experience_year',
                    'experience_month', 'current_company', 'current_working_status',
                    'current_salary', 'expected_salary', 'submit_by', 'employee_assigned',
                    'call_connection', 'calling_remark', 'lead_generate',
                    'send_for_interview', 'next_follow_up_date_time',
                    'selection_status', 'company_name', 'offered_salary',
                    'selection_date', 'candidate_joining_date', 'emta_commission',
                    'payout_date', 'selection_remark',
                    'other_lead_source', 'other_qualification', 'other_working_status',
                    'other_call_connection', 'other_lead_generate',
                    'other_interview_status', 'other_selection_status',
                    'other_origin_location', 'other_preferred_location',
                    'other_qualification', 'other_sector', 'other_department'
                ]
                
                # Capture original values for fields_to_track, converting non-serializable types
                original_candidate_serializable_data = {}
                for field_name_to_track in fields_to_track:
                    value = getattr(original_candidate, field_name_to_track)
                    if isinstance(value, (dt.date, dt.datetime)):
                        original_candidate_serializable_data[field_name_to_track] = str(value)
                    else:
                        original_candidate_serializable_data[field_name_to_track] = value

                # Handle file fields separately to ensure their names are stored, not FieldFile objects
                file_fields_to_track = ['candidate_photo', 'candidate_resume']
                for file_field_name in file_fields_to_track:
                    file_object = getattr(original_candidate, file_field_name)
                    original_candidate_serializable_data[file_field_name] = file_object.name if file_object else None

                # Apply updates from POST data to the candidate object
                candidate.candidate_name = request.POST.get('candidate_name')
                candidate.candidate_mobile_number = request.POST.get('candidate_mobile_number')
                candidate.candidate_email_address = request.POST.get('candidate_email_address')
                candidate.gender = request.POST.get('gender')
                candidate.lead_source = request.POST.get('lead_source')
                candidate.employee_assigned = request.POST.get('employee_assigned') # This field is unique to admin view

                # Multi-selects
                candidate.preferred_location = ', '.join(request.POST.getlist('preferred_location'))
                candidate.preferred_state = ', '.join(request.POST.getlist('preferred_state'))
                candidate.origin_location = request.POST.get('origin_location')
                candidate.qualification = request.POST.get('qualification')
                candidate.diploma = request.POST.get('diploma')
                candidate.sector = ', '.join(request.POST.getlist('sector'))
                candidate.department = ', '.join(request.POST.getlist('department'))

                candidate.experience_year = request.POST.get('experience_year')
                candidate.experience_month = request.POST.get('experience_month')
                candidate.current_company = request.POST.get('current_company')
                candidate.current_working_status = request.POST.get('current_working_status')
                candidate.current_salary = request.POST.get('current_salary')
                candidate.current_salary_type = request.POST.get('current_salary_type')
                candidate.expected_salary = request.POST.get('expected_salary')
                candidate.expected_salary_type = request.POST.get('expected_salary_type')
                candidate.submit_by = request.POST.get('submit_by')

                candidate.call_connection = request.POST.get('call_connection')
                candidate.calling_remark = request.POST.get('calling_remark')
                candidate.lead_generate = request.POST.get('lead_generate')
                candidate.send_for_interview = request.POST.get('send_for_interview')
                candidate.next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None

                candidate.selection_status = request.POST.get('selection_status')
                candidate.company_name = request.POST.get('company_name')
                candidate.job_title = request.POST.get('job_title')
                candidate.offered_salary = request.POST.get('offered_salary')
                candidate.selection_date = request.POST.get('selection_date') or None
                candidate.candidate_joining_date = request.POST.get('candidate_joining_date') or None
                candidate.emta_commission = request.POST.get('emta_commission')
                candidate.payout_date = request.POST.get('payout_date') or None
                candidate.joining_status = request.POST.get('joining_status')
                candidate.selection_remark = request.POST.get('selection_remark')

                candidate.other_lead_source = request.POST.get('other_lead_source')
                candidate.other_qualification = request.POST.get('other_qualification')
                candidate.other_working_status = request.POST.get('other_working_status')
                candidate.other_call_connection = request.POST.get('other_call_connection')
                candidate.other_lead_generate = request.POST.get('other_lead_generate')
                candidate.other_interview_status = request.POST.get('other_interview_status')
                candidate.other_selection_status = request.POST.get('other_selection_status')
                candidate.other_origin_location = request.POST.get('other_origin_location')
                candidate.other_preferred_location = request.POST.get('other_preferred_location')
                candidate.other_qualification = request.POST.get('other_qualification')
                candidate.other_sector = request.POST.get('other_sector')
                candidate.other_department = request.POST.get('other_department')

                # Handle file uploads and clearing
                if 'candidate_photo' in request.FILES:
                    candidate.candidate_photo = request.FILES['candidate_photo']
                elif request.POST.get('candidate_photo-clear') == 'on':
                    candidate.candidate_photo = None

                if 'candidate_resume' in request.FILES:
                    candidate.candidate_resume = request.FILES['candidate_resume']
                elif request.POST.get('candidate_resume-clear') == 'on':
                    candidate.candidate_resume = None

                candidate.updated_by = logged_in_employee # Assuming you have an 'updated_by' field in Candidate model
                candidate.save() # Save the candidate after all updates

                # Now, after saving, re-check the file fields for changes
                for field_name in fields_to_track:
                    new_value_current_object = getattr(candidate, field_name) # Get from the updated object
                    new_value_for_log = None
                    if isinstance(new_value_current_object, (dt.date, dt.datetime)):
                        new_value_for_log = str(new_value_current_object)
                    else:
                        new_value_for_log = new_value_current_object

                    old_value_serializable = original_candidate_serializable_data.get(field_name)
                    
                    if str(old_value_serializable) != str(new_value_for_log):
                        changes[field_name] = {
                            'old': old_value_serializable,
                            'new': new_value_for_log
                        }

                # Handle file changes for logging (after save, use the updated candidate object)
                if original_candidate_serializable_data.get('candidate_photo') != (candidate.candidate_photo.name if candidate.candidate_photo else None):
                    changes['candidate_photo'] = {
                        'old': original_candidate_serializable_data.get('candidate_photo'),
                        'new': candidate.candidate_photo.name if candidate.candidate_photo else None
                    }
                if original_candidate_serializable_data.get('candidate_resume') != (candidate.candidate_resume.name if candidate.candidate_resume else None):
                    changes['candidate_resume'] = {
                        'old': original_candidate_serializable_data.get('candidate_resume'),
                        'new': candidate.candidate_resume.name if candidate.candidate_resume else None
                    }

                if changes:
                    EVMS_CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action='updated',
                        changes=changes,
                        remark="Updated via unified form"
                    )
                messages.success(request, 'Candidate details updated successfully!')

            elif 'submit_vendor_related_data' in request.POST:
                # Store original data for change tracking
                original_candidate = Candidate.objects.get(id=id)
                changes = {}
                fields_to_track = [
                    'admin_status', 'vendor_commission', 'vendor_payout_date', 
                    'commission_generation_date', 'vendor_commission_status', 
                    'vendor_payment_remark', 'payment_done_by', 'payment_done_by_date'
                ]

                # Capture original values
                original_vendor_data = {}
                for field_name in fields_to_track:
                    value = getattr(original_candidate, field_name)
                    original_vendor_data[field_name] = str(value) if isinstance(value, (dt.date, dt.datetime)) else value
                
                old_submit_recipt_name = original_candidate.submit_recipt.name if original_candidate.submit_recipt else None

                # Update candidate object
                candidate.admin_status = request.POST.get('admin_status')
                candidate.vendor_commission = request.POST.get('vendor_commission')
                candidate.vendor_payout_date = request.POST.get('vendor_payout_date') or None
                candidate.commission_generation_date = request.POST.get('commission_generation_date') or None
                candidate.vendor_commission_status = request.POST.get('vendor_commission_status')
                candidate.vendor_payment_remark = request.POST.get('vendor_payment_remark')
                candidate.payment_done_by = request.POST.get('payment_done_by')
                candidate.payment_done_by_date = request.POST.get('payment_done_by_date') or None
                
                if 'submit_recipt' in request.FILES:
                    candidate.submit_recipt = request.FILES['submit_recipt']
                elif request.POST.get('submit_recipt-clear') == 'on':
                    candidate.submit_recipt = None

                candidate.updated_by = logged_in_employee
                candidate.save()

                # Track changes after saving
                for field_name in fields_to_track:
                    new_value = getattr(candidate, field_name)
                    new_value_for_log = str(new_value) if isinstance(new_value, (dt.date, dt.datetime)) else new_value
                    if str(original_vendor_data.get(field_name)) != str(new_value_for_log):
                        changes[field_name] = {'old': original_vendor_data.get(field_name), 'new': new_value_for_log}
                
                if old_submit_recipt_name != (candidate.submit_recipt.name if candidate.submit_recipt else None):
                    changes['submit_recipt'] = {
                        'old': old_submit_recipt_name,
                        'new': candidate.submit_recipt.name if candidate.submit_recipt else None
                    }

                if changes:
                    EVMS_CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action='vendor_details_updated',
                        changes=changes,
                        remark="Vendor related details updated"
                    )
                messages.success(request, 'Vendor related details updated successfully!')

            elif 'invoice_releted_data' in request.POST:
                # Store original data for change tracking
                original_candidate = Candidate.objects.get(id=id)
                changes = {}
                fields_to_track = [
                    'invoice_status', 'invoice_date', 'invoice_amount', 
                    'invoice_remark', 'invoice_paid_status', 'invoice_number'
                ]

                # Capture original values
                original_invoice_data = {}
                for field_name in fields_to_track:
                    value = getattr(original_candidate, field_name)
                    original_invoice_data[field_name] = str(value) if isinstance(value, (dt.date, dt.datetime)) else value
                
                old_invoice_attachment_name = original_candidate.invoice_attachment.name if original_candidate.invoice_attachment else None

                # Update candidate object
                candidate.invoice_status = request.POST.get('invoice_status')
                candidate.invoice_date = request.POST.get('invoice_date') or None
                candidate.invoice_amount = request.POST.get('invoice_amount')
                candidate.invoice_remark = request.POST.get('invoice_remark')
                candidate.invoice_paid_status = request.POST.get('invoice_paid_status')
                candidate.invoice_number = request.POST.get('invoice_number')
                
                if 'invoice_attachment' in request.FILES:
                    candidate.invoice_attachment = request.FILES['invoice_attachment']
                elif request.POST.get('clear_invoice_attachment') == 'on':
                    candidate.invoice_attachment = None

                candidate.updated_by = logged_in_employee
                candidate.save()

                # Track changes after saving
                for field_name in fields_to_track:
                    new_value = getattr(candidate, field_name)
                    new_value_for_log = str(new_value) if isinstance(new_value, (dt.date, dt.datetime)) else new_value
                    if str(original_invoice_data.get(field_name)) != str(new_value_for_log):
                        changes[field_name] = {'old': original_invoice_data.get(field_name), 'new': new_value_for_log}
                
                if old_invoice_attachment_name != (candidate.invoice_attachment.name if candidate.invoice_attachment else None):
                    changes['invoice_attachment'] = {
                        'old': old_invoice_attachment_name,
                        'new': candidate.invoice_attachment.name if candidate.invoice_attachment else None
                    }

                if changes:
                    CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action='invoice_updated',
                        changes=changes,
                        remark="Invoice details updated"
                    )
                messages.success(request, 'Invoice related details updated successfully!')

            elif 'add_interview_submit' in request.POST:
                try:
                    interview_date_time_str = request.POST.get('interview_date_time')
                    if interview_date_time_str:
                        interview_date_time = dt.datetime.strptime(interview_date_time_str, '%Y-%m-%dT%H:%M')
                    else:
                        interview_date_time = None

                    interview = EVMS_Candidate_Interview.objects.create(
                        candidate=candidate,
                        interview_date_time=interview_date_time,
                        company_name=request.POST.get('interview_company_name'),
                        job_position=request.POST.get('job_position'),
                        interviewer_name=request.POST.get('interviewer_name'),
                        interviewer_email=request.POST.get('interviewer_email'),
                        interviewer_phone=request.POST.get('interviewer_phone'),
                        status=request.POST.get('status'),
                        interview_mode=request.POST.get('interview_mode'),
                        location=request.POST.get('location'),
                        meeting_link=request.POST.get('meeting_link'),
                        notes=request.POST.get('notes'),
                        feedback=request.POST.get('feedback'),
                        rating=request.POST.get('rating') or None,
                        is_technical=request.POST.get('is_technical') == 'on',
                        duration=request.POST.get('duration') or None,
                        requirements=request.POST.get('requirements'),
                        created_by=request.user, 
                        updated_by=request.user, 
                    )
                    if 'interview_attachment' in request.FILES:
                        interview.attachment = request.FILES['interview_attachment']
                        interview.save()
                    EVMS_CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action=f'New interview added (ID: {interview.id})',
                        changes={
                            'interview_date_time': str(interview.interview_date_time),
                            'company_name': interview.company_name,
                            'job_position': interview.job_position,
                            'status': interview.status,
                            'interview_mode': interview.interview_mode,
                            'attachment': interview.attachment.name if interview.attachment else None
                        },
                        remark=f"New interview added by {logged_in_employee.user.username}"
                    )
                    messages.success(request, 'Interview added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding interview: {e}')
                return redirect('evms_candidate_profile', id=id)

            elif 'edit_interview_submit' in request.POST:
                interview_id = request.POST.get('interview_id')
                # This line is where the ValueError occurred. It is now corrected.
                interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id, candidate=candidate)
                original_interview_data = {}
                for field in interview._meta.fields:
                    value = getattr(interview, field.name)
                    if isinstance(value, FieldFile):
                        original_interview_data[field.name] = value.name if value else None
                    elif isinstance(value, (dt.date, dt.datetime)):
                        original_interview_data[field.name] = str(value)
                    else:
                        original_interview_data[field.name] = value
                interview_changes = {}

                interview_date_time_str = request.POST.get('interview_date_time')
                if interview_date_time_str:
                    interview.interview_date_time = dt.datetime.strptime(interview_date_time_str, '%Y-%m-%dT%H:%M')
                else:
                    interview.interview_date_time = None
                
                interview.company_name = request.POST.get('interview_company_name')
                interview.job_position = request.POST.get('job_position')
                interview.interviewer_name = request.POST.get('interviewer_name')
                interview.interviewer_email = request.POST.get('interviewer_email')
                interview.interviewer_phone = request.POST.get('interviewer_phone')
                interview.status = request.POST.get('status')
                interview.interview_mode = request.POST.get('interview_mode')
                interview.location = request.POST.get('location')
                interview.meeting_link = request.POST.get('meeting_link')
                interview.notes = request.POST.get('notes')
                interview.feedback = request.POST.get('feedback')
                interview.rating = request.POST.get('rating') or None
                interview.is_technical = request.POST.get('is_technical') == 'on'
                interview.duration = request.POST.get('duration') or None
                interview.requirements = request.POST.get('requirements')
                if 'interview_attachment' in request.FILES:
                    interview.attachment = request.FILES['interview_attachment']
                elif request.POST.get('clear_interview_attachment') == 'on': 
                    interview.attachment = None
                
                interview.updated_by = request.user
                interview.save()
                updated_interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id, candidate=candidate)
                
                for field_name in original_interview_data.keys():
                    old_value = original_interview_data[field_name]
                    new_value_current_object = getattr(updated_interview, field_name)
                    new_value_for_log = None
                    if isinstance(new_value_current_object, FieldFile):
                        new_value_for_log = new_value_current_object.name if new_value_current_object else None
                    elif isinstance(new_value_current_object, (dt.date, dt.datetime)):
                        new_value_for_log = str(new_value_current_object)
                    else:
                        new_value_for_log = new_value_current_object
                    if old_value != new_value_for_log:
                        interview_changes[field_name] = {'old': old_value, 'new': new_value_for_log}
                
                if interview_changes:
                    EVMS_CandidateActivity.objects.create(
                        candidate=candidate,
                        employee=logged_in_employee,
                        action=f'Interview updated (ID: {interview.id})',
                        changes=interview_changes,
                        remark=f"Interview details updated by {logged_in_employee.user.username}"
                    )
                messages.success(request, 'Interview updated successfully!')
                return redirect('evms_candidate_profile', id=id)

            elif 'delete_interview_submit' in request.POST:
                interview_id = request.POST.get('interview_id')
                # This line is where the ValueError occurred. It is now corrected.
                interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id, candidate=candidate)
                interview_details_for_log = {
                    'company_name': interview.company_name,
                    'job_position': interview.job_position,
                    'interview_date_time': str(interview.interview_date_time) if interview.interview_date_time else None,
                    'attachment_name': interview.attachment.name if interview.attachment else None
                }
                interview.delete()
                EVMS_CandidateActivity.objects.create(
                    candidate=candidate,
                    employee=logged_in_employee,
                    action=f'Interview deleted',
                    changes={'deleted_interview': interview_details_for_log},
                    remark=f"Interview deleted by {logged_in_employee.user.username}"
                )
                messages.success(request, 'Interview deleted successfully!')
                return redirect('evms_candidate_profile', id=id)
            
            return redirect('evms_candidate_profile', id=id)

        # GET request context
        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"
        ]

        state = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat", "Haryana", 
            "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", 
            "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu", 
            "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
        ]

        state_district = {
            "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari"], 
            "Arunachal Pradesh": ["Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang"],
            "Assam": ["Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong"],
            "Bihar": ["Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran"],
            "Chhattisgarh": ["Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur"],
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
            "Andaman and Nicobar Islands": ["Nicobar", "North and Middle Andaman", "South Andaman"],
            "Chandigarh": ["Chandigarh"],
            "Dadra and Nagar Haveli and Daman and Diu": ["Dadra and Nagar Haveli", "Daman", "Diu"],
            "Delhi": ["Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi"],
            "Jammu and Kashmir": ["Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur"],
            "Ladakh": ["Kargil", "Leh"],
            "Lakshadweep": ["Lakshadweep"],
            "Puducherry": ["Karaikal", "Mahe", "Puducherry", "Yanam"]
        }

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
            "Software Development", "IT Support", "Web Development", 
            "Network Administration", "Cybersecurity", 
            "Data Science & Analytics", "Cloud Computing", "Quality Assurance (QA)",
            "Customer Support", "Technical Support", "Voice Process", 
            "Non-Voice Process", "Back Office Operations",
            "Investment Banking", "Retail Banking", "Loan Processing", 
            "Risk Management", "Accounting and Auditing", 
            "Financial Analysis", "Wealth Management",
            "Medical Representatives", "Clinical Research", "Nursing", 
            "Medical Technicians", "Pharmacy Operations", 
            "Healthcare Administration",
            "Teaching", "Curriculum Development", "Academic Counseling", 
            "E-Learning Development", "Education Administration",
            "Store Operations", "Supply Chain Management", 
            "Sales and Merchandising", "E-commerce Operations", "Digital Marketing",
            "Production Planning", "Quality Control", "Maintenance and Repair", 
            "Operations Management", "Inventory Management",
            "Sales and Marketing", "Civil Engineering", "Project Management", 
            "Interior Designing", "Surveying and Valuation",
            "Hotel Management", "Travel Coordination", "Event Planning", 
            "Food and Beverage Services", "Guest Relations",
            "Content Writing", "Video Editing", "Graphic Designing", 
            "Social Media Management", "Event Production",
            "Network Installation", "Customer Support", "Telecom Engineering", 
            "Technical Operations", "Business Development",
            "Logistics Coordination", "Warehouse Management", "Procurement", 
            "Transportation Management", "Inventory Control",
            "Market Research", "Brand Management", "Advertising Sales", 
            "Public Relations", "Digital Marketing",
            "Recruitment", "Employee Relations", "Payroll and Benefits", 
            "Training and Development", "HR Analytics",
            "Corporate Law", "Compliance Auditing", "Contract Management", 
            "Intellectual Property Rights", "Legal Advisory",
            "Civil Engineering", "Mechanical Engineering", 
            "Electrical Engineering", "Project Planning", "Structural Design",
            "Automotive Design", "Production and Assembly", "Sales and Service", 
            "Supply Chain Management", "Quality Assurance",
            "Fashion Design", "Merchandising", "Production Management", 
            "Quality Control", "Retail Sales",
            "Sales and Marketing", "Supply Chain Operations", 
            "Production Management", "Quality Control", "Brand Management",
            "Agribusiness Management", "Farm Operations", "Food Processing", 
            "Agricultural Sales", "Quality Assurance",
            "Sales and Business Development", "Underwriting", 
            "Claims Management", "Actuarial Services", "Policy Administration",
            "Administrative Services", "Public Relations", 
            "Policy Analysis", "Clerical Positions", "Field Operations",
            "Community Development", "Fundraising", "Program Management", 
            "Volunteer Coordination", "Policy Advocacy",
            "Renewable Energy Operations", "Power Plant Engineering", 
            "Energy Efficiency Management", "Electrical Design", "Maintenance",
            "Aviation and Aerospace",
            "Flight Operations", "Ground Staff", "Aircraft Maintenance", 
            "Cabin Crew", "Research and Development"
        ]

        context = {
            'candidate': candidate,
            'employees': employees,
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
            'vacancies': vacancies,
            'activities': candidate.activities.all().order_by('-timestamp'),
            'interviews': candidate.interviews.all().order_by('-interview_date_time'), # Pass interviews to template
            'today': timezone.now().date(),
            'companies': companies,
            'state': state,
            'state_district': state_district,
            'interview_statuses': EVMS_Candidate_Interview.INTERVIEW_STATUS, # Assuming you have this tuple defined in EVMS_Candidate_Interview model
            'interview_modes': EVMS_Candidate_Interview.INTERVIEW_MODE,     # Assuming you have this tuple defined in EVMS_Candidate_Interview model
        }
        return render(request, 'crm/evms-candidate-profile.html', context)
    else:
        messages.error(request, "You are not authorized to view this page.")
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def evms_vendor_candidate_profile(request,id) :
    if request.user.is_staff or request.user.is_superuser:
        candidate = get_object_or_404(Candidate, id=id)
        employees = Employee.objects.all()
        companies = Company_registration.objects.all()
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
                next_follow_up_date_time = request.POST.get('next_follow_up_date_time')
                submit_by = request.POST.get('submit_by')

                candidate.call_connection = call_connection
                candidate.calling_remark = calling_remark
                candidate.lead_generate = lead_generate
                candidate.send_for_interview = send_for_interview
                candidate.next_follow_up_date_time = next_follow_up_date_time
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
        vacancies = VacancyDetails.objects.filter(
            vacancy_status='Active'
        ).select_related('company').values(
            'id',
            'job_profile',
            'company__company_name'
        )
        context = {
            'candidate': candidate,
            'employees' : employees,
            'companies': companies,
            'vacancies': vacancies,
        }
        return render(request,'crm/evms-vendor-candidate-profile.html',context)

@login_required(login_url='/crm/404/')
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

@login_required(login_url='/crm/404/')
def admin_company_registration(request):
    if request.user.is_staff or request.user.is_superuser:
        if request.method == 'POST':
            # Capture company data
            # employee_name = request.POST.get('employee_name')
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
            attech_proposal = request.FILES.get('attech_proposal') 
            remark = request.POST.get('remark')

            # Create or update company
            company, created = Company_registration.objects.get_or_create(
                company_unique_code=company_unique_code,
                created_by = request.user,
                defaults={
                    # 'employee_name': employee_name,
                    'company_name': company_name,
                    'company_logo': company_logo,
                    'company_location': company_location,
                    'company_email_address': company_email_address,
                    'company_contact_person_name': company_contact_person_name,
                    'company_contact_person_contact_details': company_contact_person_contact_details,
                    'company_contact_person_designation': company_contact_person_designation,
                    'interview_address': interview_address,
                    'status_of_proposal': status_of_proposal,
                    'attech_proposal': attech_proposal,
                    'remark': remark,
                    
                }
            )

            messages.success(request, 'Company added successfully!')

            # If company exists but fields are different, update them
            if not created:
                # company.employee_name = employee_name
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
                company.remark = remark
                if attech_proposal:
                    company.attech_proposal = attech_proposal
                company.save()

            # Return JSON response for AJAX handling
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Company added successfully!',
                    'redirect_url': reverse('admin_company_list')
                })
            
            messages.success(request, 'Company added successfully!')
            return redirect('admin_company_list')
        
        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"

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

        # Render the template with the context
        return render(request, 'crm/company-registration.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_vendor_profile(request, id):
    if request.user.is_staff or request.user.is_superuser:
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
                vendor.user.email = request.POST.get('email')
                vendor.user.save()
                vendor.mobile_number = request.POST.get('mobile_number')
                vendor.date_of_birth = request.POST.get('date_of_birth')
                vendor.profileVerification = request.POST.get('profileVerification')
                vendor.verification_remark = request.POST.get('verification_remark')
                
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
                vendor_profile_detail.updated_by=request.user
                
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
                return redirect('admin_vendor_profile', id=vendor.id)

        districts = [
            "Alirajpur", "Anuppur", "Ashoknagar", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal",
            "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori",
            "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni",
            "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Narsinghpur", "Neemuch",
            "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni",
            "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh",
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"

        ]
        


        context = {
            'vendor': vendor,
            'vendor_profile_detail': vendor_profile_detail,
            'vendor_bussiness_detail': vendor_bussiness_detail,
            'vendor_bank_detail': vendor_bank_detail,
            'districts' : districts,
            'candidates' : candidates
        }
        return render(request, 'crm/evms-vendor-profile.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_evms_vendor_paylist(request):
    if request.user.is_staff or request.user.is_superuser:
        # Get current month and year
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        
        # Filter candidates with refer_code, pending commission, and payout date in current month
        remaining_pays = Candidate.objects.filter(
            vendor_commission_status__in=['Pending', 'In Process', 'Failed'],
            selection_status='Selected',
            refer_code__isnull=False,
            # vendor_payout_date__month=current_month,
            # vendor_payout_date__year=current_year
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
        return render(request, 'crm/vendor-pay-list.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_evms_vendor_transaction_history(request):
    if request.user.is_staff or request.user.is_superuser:
    
        # Filter candidates with refer_code, pending commission, and payout date in current month
        remaining_pays = Candidate.objects.filter(
            vendor_commission_status__in=['Paid', 'Failed'],
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
        return render(request, 'crm/vendor-transaction-history.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def admin_export_vendors_to_excel(request):
    if request.user.is_staff or request.user.is_superuser:
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
        return render(request, 'crm/404.html', status=404)

import datetime as sc

# Helper function to parse date ranges
def parse_date_range(date_range_str):
    """Parses a 'YYYY-MM-DD to YYYY-MM-DD' string into start and end dates."""
    if ' to ' in date_range_str:
        try:
            start_str, end_str = date_range_str.split(' to ')
            start_date = sc.datetime.strptime(start_str, '%Y-%m-%d').date()
            # Add 1 day to end_date to make the range inclusive
            end_date = sc.datetime.strptime(end_str, '%Y-%m-%d').date() + sc.timedelta(days=1)
            return start_date, end_date
        except ValueError:
            pass
    return None, None

@login_required(login_url='/crm/404/')
def selected_candidate(request) :
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    # --- Get Filter Parameters ---
    search_query = request.GET.get('search', '')
    company_filters = request.GET.getlist('company')
    employee_filters = request.GET.getlist('employee')
    selection_date_range = request.GET.get('selection_date', '')
    joining_date_range = request.GET.get('joining_date', '')

    # --- Build Base Q objects ---
    reg_filters = Q(selection_status='Selected')
    can_filters = Q(selection_status='Selected')

    # 1. Search Filter
    if search_query:
        search_q = (
            Q(candidate_name__icontains=search_query) |
            Q(unique_code__icontains=search_query) |
            Q(candidate_mobile_number__icontains=search_query) |
            Q(candidate_email_address__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
        reg_filters &= search_q
        can_filters &= search_q

    # 2. Company Filter
    if company_filters:
        reg_filters &= Q(company_name__in=company_filters)
        can_filters &= Q(company_name__in=company_filters)

    # 3. Employee Filter
    if employee_filters:
        reg_filters &= Q(employee_name__in=employee_filters)
        can_filters &= Q(employee_name__in=employee_filters)

    # 4. Selection Date Range
    start_sel, end_sel = parse_date_range(selection_date_range)
    if start_sel and end_sel:
        reg_filters &= Q(selection_date__gte=start_sel, selection_date__lt=end_sel)
        can_filters &= Q(selection_date__gte=start_sel, selection_date__lt=end_sel)

    # 5. Joining Date Range
    start_join, end_join = parse_date_range(joining_date_range)
    if start_join and end_join:
        reg_filters &= Q(candidate_joining_date__gte=start_join, candidate_joining_date__lt=end_join)
        can_filters &= Q(candidate_joining_date__gte=start_join, candidate_joining_date__lt=end_join)

    # --- Apply Filters ---
    candidates_reg = Candidate_registration.objects.filter(reg_filters)
    candidates_can = Candidate.objects.filter(can_filters)

    # --- Chain, Sort, and Paginate ---
    candidates_list = list(chain(candidates_reg, candidates_can))
    
    # Sort by selection_date, putting candidates without one at the end
    candidates_list.sort(key=lambda x: x.selection_date if x.selection_date else sc.date.min, reverse=True)

    paginator = Paginator(candidates_list, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Get All Companies & Employees for Filters ---
    # Query all selected candidates *before* filtering to get all options
    reg_all = Candidate_registration.objects.filter(selection_status='Selected')
    can_all = Candidate.objects.filter(selection_status='Selected')

    all_employees = sorted(list(set(
        [name for name in reg_all.values_list('employee_name', flat=True) if name] +
        [name for name in can_all.values_list('employee_name', flat=True) if name]
    )))
    
    all_companies = sorted(list(set(
        [name for name in reg_all.values_list('company_name', flat=True) if name] +
        [name for name in can_all.values_list('company_name', flat=True) if name]
    )))

    # --- Build Context ---
    context = {
        'page_obj': page_obj,
        'all_employees': all_employees,
        'all_companies': all_companies,
        
        # Pass current filters back to pre-fill the form
        'current_search': search_query,
        'current_companies': company_filters,
        'current_employees': employee_filters,
        'current_selection_date': selection_date_range,
        'current_joining_date': joining_date_range,
        
        # Build query string for pagination links
        'filter_query_string': request.GET.urlencode().replace('&page=' + str(page_number), ''),
    }
    return render(request, 'crm/selected-candidate.html', context)

import datetime as fuc

@login_required(login_url='/crm/404/')
def follow_up_candidate(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    today = timezone.now().date()
    start_of_today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # --- Get Filter Parameters ---
    search_query = request.GET.get('search', '')
    employee_filters = request.GET.getlist('employee')
    date_range_str = request.GET.get('date_range', '')
    lead_status_filter = request.GET.get('lead_status', '')
    follow_up_status_filter = request.GET.get('follow_up_status', '')

    # --- Build Base Q objects ---
    reg_filters = Q(next_follow_up_date_time__isnull=False)
    can_filters = Q(next_follow_up_date_time__isnull=False)

    # 1. Search Filter
    if search_query:
        reg_filters &= (
            Q(candidate_name__icontains=search_query) |
            Q(unique_code__icontains=search_query) |
            Q(candidate_mobile_number__icontains=search_query) |
            Q(candidate_email_address__icontains=search_query)
        )
        can_filters &= (
            Q(candidate_name__icontains=search_query) |
            Q(candidate_mobile_number__icontains=search_query) |
            Q(candidate_email_address__icontains=search_query)
        )

    # 2. Employee Filter
    if employee_filters:
        reg_filters &= Q(employee_name__in=employee_filters)
        can_filters &= Q(employee_name__in=employee_filters)

    # 3. Lead Status Filter
    if lead_status_filter:
        reg_filters &= Q(lead_generate=lead_status_filter)
        can_filters &= Q(lead_generate=lead_status_filter)

    # 4. Date Range & Follow-up Status Filters (These are related)
    if date_range_str:
        # If a specific date range is given, it overrides other date filters
        try:
            start_str, end_str = date_range_str.split(' to ')
            start_date = fuc.datetime.strptime(start_str, '%Y-%m-%d').date()
            # Add 1 day to end_date to make the range inclusive
            end_date = fuc.datetime.strptime(end_str, '%Y-%m-%d').date() + fuc.timedelta(days=1)
            
            reg_filters &= Q(next_follow_up_date_time__gte=start_date, next_follow_up_date_time__lt=end_date)
            can_filters &= Q(next_follow_up_date_time__gte=start_date, next_follow_up_date_time__lt=end_date)
        except ValueError:
            pass # Ignore badly formatted date range
            
    elif follow_up_status_filter:
        # If no date range, but follow-up status is given
        if follow_up_status_filter == 'overdue':
            reg_filters &= Q(next_follow_up_date_time__lt=start_of_today)
            can_filters &= Q(next_follow_up_date_time__lt=start_of_today)
        elif follow_up_status_filter == 'today':
            tomorrow = start_of_today + fuc.timedelta(days=1)
            reg_filters &= Q(next_follow_up_date_time__gte=start_of_today, next_follow_up_date_time__lt=tomorrow)
            can_filters &= Q(next_follow_up_date_time__gte=start_of_today, next_follow_up_date_time__lt=tomorrow)
        elif follow_up_status_filter == 'upcoming':
            tomorrow = start_of_today + fuc.timedelta(days=1)
            reg_filters &= Q(next_follow_up_date_time__gte=tomorrow)
            can_filters &= Q(next_follow_up_date_time__gte=tomorrow)
            
    else:
        # DEFAULT: If no date filters are applied, use the original 5-day window
        date_range_start = today - fuc.timedelta(days=2)
        # Add 1 day to end_date to make it inclusive
        date_range_end = today + fuc.timedelta(days=4) # 3 days from today + 1 for 'lt'
        
        reg_filters &= Q(next_follow_up_date_time__gte=date_range_start, next_follow_up_date_time__lt=date_range_end)
        can_filters &= Q(next_follow_up_date_time__gte=date_range_start, next_follow_up_date_time__lt=date_range_end)

    # --- Apply Filters to Querysets ---
    candidates_reg = Candidate_registration.objects.filter(reg_filters)
    candidates_can = Candidate.objects.filter(can_filters)

    # --- Chain, Sort, and Paginate ---
    candidates_list = list(chain(candidates_reg, candidates_can))
    
    # Sort the combined list in Python (by the follow-up date)
    candidates_list.sort(key=lambda x: x.next_follow_up_date_time)

    paginator = Paginator(candidates_list, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Get All Employees & Statuses for Filters ---
    # We query *before* filtering to show all possible filter options
    reg_employees = Candidate_registration.objects.values_list('employee_name', flat=True).distinct()
    can_employees = Candidate.objects.values_list('employee_name', flat=True).distinct()
    all_employees = sorted(list(set(
        [name for name in list(reg_employees) if name] + 
        [name for name in list(can_employees) if name]
    )))
    
    reg_statuses = Candidate_registration.objects.values_list('lead_generate', flat=True).distinct()
    can_statuses = Candidate.objects.values_list('lead_generate', flat=True).distinct()
    all_lead_statuses = sorted(list(set(
        [status for status in list(reg_statuses) if status] +
        [status for status in list(can_statuses) if status]
    )))

    # --- Build Context ---
    context = {
        'page_obj': page_obj,  # Pass the paginated page object
        'today': today,
        'start_of_today': start_of_today,
        'all_employees': all_employees,
        'all_lead_statuses': all_lead_statuses,
        
        # Pass current filters back to pre-fill the form
        'current_search': search_query,
        'current_employees': employee_filters,
        'current_date_range': date_range_str,
        'current_lead_status': lead_status_filter,
        'current_follow_up_status': follow_up_status_filter,

        
        # Build query string for pagination links to preserve filters
        'filter_query_string': request.GET.urlencode().replace('&page=' + str(page_number), ''),
    }
    return render(request, 'crm/follow-up-candidate.html', context)

import datetime as gl
@login_required(login_url='/crm/404/')
def generated_leads(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    # --- Get Filter Parameters from GET request ---
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    employee_filters = request.GET.getlist('employee')  # Use getlist for multiple checkboxes
    date_range_str = request.GET.get('date_range', '')

    # --- Build Filter Q objects ---
    reg_filters = Q()
    can_filters = Q()

    # 1. Status Filter
    if status_filter:
        reg_filters &= Q(lead_generate=status_filter)
        can_filters &= Q(lead_generate=status_filter)
    else:
        # Default to 'Hot' and 'Converted' if no status is selected
        reg_filters &= Q(lead_generate__in=['Hot', 'Converted'])
        can_filters &= Q(lead_generate__in=['Hot', 'Converted'])

    # 2. Search Filter
    if search_query:
        # Assumes fields to search on. Adjust field names if necessary.
        reg_filters &= (
            Q(candidate_name__icontains=search_query) |
            Q(unique_code__icontains=search_query) |
            Q(candidate_mobile_number__icontains=search_query) |
            Q(candidate_email_address__icontains=search_query)
        )
        # Assumes Candidate model has similar fields
        can_filters &= (
            Q(candidate_name__icontains=search_query) |
            Q(candidate_mobile_number__icontains=search_query) |
            Q(candidate_email_address__icontains=search_query)
        )

    # 3. Employee Filter
    if employee_filters:
        reg_filters &= Q(employee_name__in=employee_filters)
        can_filters &= Q(employee_name__in=employee_filters)

    # 4. Date Range Filter
    start_date = None
    end_date = None
    if ' to ' in date_range_str:
        try:
            start_str, end_str = date_range_str.split(' to ')
            start_date = gl.datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = gl.datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            start_date, end_date = None, None  # Ignore bad format

    if start_date and end_date:
        # Add 1 day to end_date to make the range inclusive for datetime
        end_date_inclusive = end_date + gl.timedelta(days=1)
        reg_filters &= Q(register_time__gte=start_date, register_time__lt=end_date_inclusive)
        can_filters &= Q(register_time__gte=start_date, register_time__lt=end_date_inclusive)

    # --- Apply Filters to Base Querysets ---
    candidates_reg = Candidate_registration.objects.filter(reg_filters)
    candidates_can = Candidate.objects.filter(can_filters)

    # --- Chain, Sort, and Paginate ---
    # This part is expensive as it loads all data into memory to sort.
    # This is unavoidable with your current two-model structure.
    candidates_list = list(chain(candidates_reg, candidates_can))
    
    # Sort the combined list in Python
    candidates_list.sort(key=lambda x: x.register_time, reverse=True)

    paginator = Paginator(candidates_list, 20)  # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Get Employee List for Filter Dropdown ---
    # This must be done *before* filtering to show all available employees
    reg_employees = Candidate_registration.objects.values_list('employee_name', flat=True).distinct()
    can_employees = Candidate.objects.values_list('employee_name', flat=True).distinct()
    
    # Combine, remove None/empty, get unique, and sort
    all_employees = sorted(list(set(
        [name for name in list(reg_employees) if name] + 
        [name for name in list(can_employees) if name]
    )))

    # --- Build Context ---
    context = {
        'page_obj': page_obj,  # Pass the paginated page object
        'all_employees': all_employees,
        
        # Pass current filters back to pre-fill the form
        'current_search': search_query,
        'current_status': status_filter,
        'current_employees': employee_filters,
        'current_date_range': date_range_str,
        
        # Build query string for pagination links to preserve filters
        'filter_query_string': request.GET.urlencode().replace('&page=' + str(page_number), ''),
    }
    return render(request, 'crm/lead-generate.html', context)

@login_required(login_url='/crm/404/')
def admin_vacancy_list(request) :
    if request.user.is_staff or request.user.is_superuser:
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
        return render(request, 'crm/vacancy-list.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required(login_url='/crm/404/')
def crm_admin_profile(request,id):
    if request.user.is_staff or request.user.is_superuser:
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
                employee.updated_by=request.user
                if employee_photo:
                    employee.employee_photo = employee_photo
                employee.save()

                # Update EmployeeAdditionalInfo fields
                date_of_birth = request.POST.get('date_of_birth')
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
                additional_info.updated_by=request.user
                additional_info.save()

                messages.success(request, 'Employee details updated successfully!')

            elif 'sumbit_family_details' in request.POST:
                # Handle Emergency Contact fields
                member_name = request.POST.get('member_name')
                relation = request.POST.get('relation')
                contact_number = request.POST.get('contact_number')
                date_of_birth = request.POST.get('date_of_birth')

                Family_details.objects.create(
                    employee=employee,
                    member_name=member_name,
                    relation=relation,
                    contact_number=contact_number,
                    date_of_birth=date_of_birth,
                    updated_by=request.user
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
                address_details.updated_by=request.user
                address_details.save()
                
                messages.success(request, 'Address details updated successfully!')
                
            elif 'submit_education_details' in request.POST:
                # Retrieve form data
                cource_name = request.POST.get('cource_name')
                institution_name = request.POST.get('institution_name')
                start_year = request.POST.get('start_year')
                end_year = request.POST.get('end_year')
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
                    education_certificate=education_certificate,
                    updated_by=request.user
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
                    experience_certificate = experience_certificate,
                    updated_by=request.user
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
                    document_file=document_file,
                    updated_by=request.user
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
                bank_details.updated_by=request.user
                bank_details.save()

                messages.success(request, 'Bank details updated successfully!')
                
                

            return redirect('crm_admin_profile', id=employee.id)  # Adjust 'employee-details' to your URL name
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
        return render(request, 'crm/admin-profile.html', context)
    else:
        return render(request, 'hrms/admin-login.html', {'error': 'User not authenticated'})

@login_required(login_url='/crm/404/')
def admin_candidate_chat_list(request, candidate_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
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
            attachment=attachment,
            created_by=request.user
        )
        messages.success(request, 'Chat record added successfully!')
        return redirect('admin_candidate_chat_list', candidate_id=candidate_id)
    
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
    return render(request, 'crm/candidate_chat_list.html', context)

@login_required(login_url='/crm/404/')
def admin_delete_chat(request, pk):
    chat = get_object_or_404(Candidate_chat, pk=pk)
    candidate_id = chat.candidate.id
    chat.delete()
    messages.success(request, 'Chat record deleted successfully!')
    return redirect('admin_candidate_chat_list', candidate_id=candidate_id)

@login_required(login_url='/crm/404/')
def admin_interview_list(request, candidate_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    candidate = get_object_or_404(Candidate_registration, id=candidate_id)
    companys = Company_registration.objects.all()
    vacancies = VacancyDetails.objects.filter(vacancy_status='Active').order_by('-id')
    
    if request.method == 'POST':
        if 'send_email' in request.POST:
            # Handle email sending
            interview_id = request.POST.get('interview_id')
            interview = get_object_or_404(Candidate_Interview, id=interview_id)
            send_interview_email(request, interview)
            messages.success(request, 'Interview details sent to candidate!')
            return redirect('admin_interview_list', candidate_id=candidate_id)
        
        # Handle form submission
        interview_date_time = request.POST.get('interview_date_time')
        company_name = request.POST.get('company_name')
        job_position = request.POST.get('job_position')
        status = request.POST.get('status')
        interview_mode = request.POST.get('interview_mode')
        notes = request.POST.get('notes')
        
        interview = Candidate_Interview(
            candidate=candidate,
            interview_date_time=interview_date_time,
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
        return redirect('admin_interview_list', candidate_id=candidate_id)
    
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
        'companys' : companys,
        'vacancies' : vacancies
    }
    return render(request, 'crm/candidate_interview_list.html', context)

@login_required(login_url='/crm/404/')
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

@login_required(login_url='/crm/404/')
def admin_interview_detail(request, interview_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    interview = get_object_or_404(Candidate_Interview, id=interview_id)
    companys = Company_registration.objects.all()
    
    if request.method == 'POST':
        # Handle update
        interview.interview_date_time = request.POST.get('interview_date_time')
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
        return redirect('admin_interview_detail', interview_id=interview.id)
    
    context = {
        'interview': interview,
        'status_choices': Candidate_Interview.INTERVIEW_STATUS,
        'mode_choices': Candidate_Interview.INTERVIEW_MODE,
        'companys' : companys
    }
    return render(request, 'crm/candidate_interview_detail.html', context)

@login_required(login_url='/crm/404/')
def admin_delete_interview(request, interview_id):
    interview = get_object_or_404(Candidate_Interview, id=interview_id)
    candidate_id = interview.candidate.id
    interview.delete()
    messages.success(request, 'Interview deleted successfully!')
    return redirect('admin_interview_list', candidate_id=candidate_id)

@login_required(login_url='/crm/404/')
def admin_company_communication_list(request, company_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
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
            communication_date=request.POST.get('communication_date') or None,
            communication_type=request.POST.get('communication_type'),
            subject=request.POST.get('subject'),
            communication_details=request.POST.get('communication_details'),
            follow_up_date=request.POST.get('follow_up_date') or None,
            priority=request.POST.get('priority', 'medium'),
            outcome=request.POST.get('outcome'),
            employee_name=request.user.get_full_name() or request.user.username,
            attachment=request.FILES.get('attachment'),
            created_by = request.user
        )
        communication.save()
        messages.success(request, 'Communication record added successfully!')
        return redirect('admin_company_communication_list', company_id=company_id)
    
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
    return render(request, 'crm/company_communication_list.html', context)

@login_required(login_url='/crm/404/')
def admin_company_communication_detail(request, communication_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    communication = get_object_or_404(company_communication, id=communication_id)
    
    if request.method == 'POST':
        # Handle update
        communication.contact_person = request.POST.get('contact_person')
        communication.designation = request.POST.get('designation')
        communication.contact_email = request.POST.get('contact_email')
        communication.contact_phone = request.POST.get('contact_phone')
        communication.communication_date = request.POST.get('communication_date') or None
        communication.communication_type = request.POST.get('communication_type')
        communication.subject = request.POST.get('subject')
        communication.communication_details = request.POST.get('communication_details')
        communication.follow_up_date = request.POST.get('follow_up_date') or None
        communication.priority = request.POST.get('priority', 'medium')
        communication.outcome = request.POST.get('outcome')
        communication.updated_by=request.user
        
        if 'attachment' in request.FILES:
            communication.attachment = request.FILES['attachment']
        
        communication.save()
        messages.success(request, 'Communication record updated successfully!')
        return redirect('admin_company_communication_detail', communication_id=communication.id)
    
    context = {
        'communication': communication,
        'communication_types': company_communication.COMMUNICATION_TYPES,
        'priority_choices': company_communication.PRIORITY_CHOICES,
    }
    return render(request, 'crm/company_communication_detail.html', context)

@login_required(login_url='/crm/404/')
def admin_delete_company_communication(request, communication_id):
    communication = get_object_or_404(company_communication, id=communication_id)
    company_id = communication.company.id
    communication.delete()
    messages.success(request, 'Communication record deleted successfully!')
    return redirect('admin_company_communication_list', company_id=company_id)

@login_required(login_url='/crm/404/')
def admin_send_communication_email(request, communication):
    """Helper function to send communication details email"""
    subject = f"Communication Record: {communication.subject}"
    
    context = {
        'communication': communication,
        'company': communication.company,
    }
    
    # Render HTML email template
    html_message = render_to_string('emails/company_communication_record.html', context)
    
    recipients = [communication.contact_email]
    if communication.company.email:
        recipients.append(communication.company.email)
    
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
    
@login_required(login_url='/crm/404/')
def admin_company_contacts_list(request, company_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    company = get_object_or_404(Company_registration, id=company_id)
    
    if request.method == 'POST':
        if 'send_email' in request.POST:
            # Handle email sending
            contact_id = request.POST.get('contact_id')
            contact = get_object_or_404(Company_spoke_person, id=contact_id)
            # Add your email sending logic here
            messages.success(request, f'Email sent to {contact.name} successfully!')
            return redirect('admin_company_contacts_list', company_id=company_id)
        
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
            created_by=request.user
        )
        contact.save()
        messages.success(request, 'Contact person added successfully!')
        return redirect('admin_company_contacts_list', company_id=company_id)
    
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
    return render(request, 'crm/contacts_list.html', context)

@login_required(login_url='/crm/404/')
def admin_company_contact_detail(request, contact_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
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
        return redirect('admin_company_contact_detail', contact_id=contact.id)
    
    context = {
        'contact': contact,
        'status_choices': Company_spoke_person.STATUS_CHOICES,
        'priority_choices': Company_spoke_person.PRIORITY_CHOICES,
    }
    return render(request, 'crm/contact_detail.html', context)

@login_required(login_url='/crm/404/')
def admin_delete_company_contact(request, contact_id):
    contact = get_object_or_404(Company_spoke_person, id=contact_id)
    company_id = contact.company.id
    contact.delete()
    messages.success(request, 'Contact person deleted successfully!')
    return redirect('admin_company_contacts_list', company_id=company_id)

import csv
from django.utils import timezone # IMPORTANT: Import timezone

@login_required(login_url='/crm/404/')
def download_candidate_details(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    # Get filter parameters from the request
    employee_name = request.GET.get('employee_name', None)
    start_date_str = request.GET.get('start_date', None)
    end_date_str = request.GET.get('end_date', None)

    # Start with base querysets
    crm_candidates = Candidate_registration.objects.all()
    evms_candidates = Candidate.objects.all()

    # Apply filters conditionally with timezone awareness
    if employee_name:
        crm_candidates = crm_candidates.filter(employee_name=employee_name)
        evms_candidates = evms_candidates.filter(employee_name=employee_name)

    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        aware_start_date = timezone.make_aware(start_date) # Make it timezone-aware
        crm_candidates = crm_candidates.filter(register_time__gte=aware_start_date)
        evms_candidates = evms_candidates.filter(register_time__gte=aware_start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_of_day = end_date + timedelta(days=1)
        aware_end_of_day = timezone.make_aware(end_of_day) # Make it timezone-aware
        crm_candidates = crm_candidates.filter(register_time__lt=aware_end_of_day)
        evms_candidates = evms_candidates.filter(register_time__lt=aware_end_of_day)
        
    # Create a dynamic filename
    filename = f"candidates_{datetime.now().strftime('%Y-%m-%d')}.csv"
    if employee_name or start_date_str or end_date_str:
        filename = f"{employee_name}_candidates_{datetime.now().strftime('%Y-%m-%d')}.csv"

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    
    header = [
        'Employee Name', 'Candidate Name', 'Unique Code', 'Mobile Number', 
        'Alternate Mobile', 'Email', 'Gender', 'Lead Source', 'Preferred Location',
        'Origin Location', 'Qualification', 'Diploma', 'Sector', 'Department',
        'Experience Year', 'Experience Month', 'Current Company', 'Working Status',
        'Current Salary', 'Expected Salary', 'Call Connection', 'Calling Remark',
        'Lead Generate', 'Send for Interview', 'Next Follow Up Date Time', 'Candidate Photo',
        'Candidate Resume', 'Remark', 'Registration Time', 'Submitted By',
        'Selection Status', 'Joining Status', 'Company Name', 'Offered Salary', 'Selection Date',
        'Joining Date', 'EMTA Commission', 'Payout Date',
        'Refer Code', 'Job Type', 'Vendor Commission', 'Vendor Payout Date', 
        'Vendor Commission Status', 'Commission Generation Date', 'Vendor Payment Remark', 
        'Admin Status', 'Payment Done By', 'Payment Done By Date', 'Submit Recipt'
    ]
    writer.writerow(header)

    all_candidates = list(crm_candidates) + list(evms_candidates)
    all_candidates.sort(key=lambda x: x.register_time if hasattr(x, 'register_time') and x.register_time else timezone.now())

    for obj in all_candidates:
        # Your entire CSV writing loop goes here
        # (This part is from your original code and is assumed to be correct)
        is_evms = isinstance(obj, Candidate)
        unique_code = getattr(obj, 'unique_code', '')
        payout_date = getattr(obj, 'payout_date', '')
        refer_code = getattr(obj, 'refer_code', '') if is_evms else ''
        job_type = getattr(obj, 'job_type', '') if is_evms else ''
        vendor_commission = getattr(obj, 'vendor_commission', '') if is_evms else ''
        vendor_payout_date = getattr(obj, 'vendor_payout_date', '') if is_evms else ''
        vendor_commission_status = getattr(obj, 'vendor_commission_status', '') if is_evms else ''
        commission_generation_date = getattr(obj, 'commission_generation_date', '') if is_evms else ''
        vendor_payment_remark = getattr(obj, 'vendor_payment_remark', '') if is_evms else ''
        admin_status = getattr(obj, 'admin_status', '') if is_evms else ''
        payment_done_by = getattr(obj, 'payment_done_by', '') if is_evms else ''
        payment_done_by_date = getattr(obj, 'payment_done_by_date', '') if is_evms else ''
        submit_recipt = str(obj.submit_recipt) if is_evms and getattr(obj, 'submit_recipt', None) else ''

        writer.writerow([
            getattr(obj, 'employee_name', ''),
            getattr(obj, 'candidate_name', ''),
            unique_code,
            getattr(obj, 'candidate_mobile_number', ''),
            getattr(obj, 'candidate_alternate_mobile_number', '') or '',
            getattr(obj, 'candidate_email_address', '') or '',
            getattr(obj, 'gender', '') or '',
            getattr(obj, 'lead_source', ''),
            getattr(obj, 'preferred_location', '') or '',
            getattr(obj, 'origin_location', '') or '',
            getattr(obj, 'qualification', '') or '',
            getattr(obj, 'diploma', '') or '',
            getattr(obj, 'sector', '') or '',
            getattr(obj, 'department', '') or '',
            getattr(obj, 'experience_year', '') or '',
            getattr(obj, 'experience_month', '') or '',
            getattr(obj, 'current_company', '') or '',
            getattr(obj, 'current_working_status', ''),
            getattr(obj, 'current_salary', '') or '',
            getattr(obj, 'expected_salary', '') or '',
            getattr(obj, 'call_connection', '') or '',
            getattr(obj, 'calling_remark', '') or '',
            getattr(obj, 'lead_generate', '') or '',
            getattr(obj, 'send_for_interview', '') or '',
            getattr(obj, 'next_follow_up_date_time', '') or '',
            str(obj.candidate_photo) if getattr(obj, 'candidate_photo', None) else '',
            str(obj.candidate_resume) if getattr(obj, 'candidate_resume', None) else '',
            getattr(obj, 'remark', '') or '',
            obj.register_time.strftime("%Y-%m-%d %H:%M:%S") if getattr(obj, 'register_time', None) else '',
            getattr(obj, 'submit_by', '') or '',
            getattr(obj, 'selection_status', ''),
            getattr(obj, 'joining_status', '') or '',
            getattr(obj, 'company_name', '') or '',
            getattr(obj, 'offered_salary', '') or '',
            getattr(obj, 'selection_date', '') or '',
            getattr(obj, 'candidate_joining_date', '') or '',
            getattr(obj, 'emta_commission', '') or '',
            payout_date,
            refer_code,
            job_type,
            vendor_commission,
            vendor_payout_date,
            vendor_commission_status,
            commission_generation_date,
            vendor_payment_remark,
            admin_status,
            payment_done_by,
            payment_done_by_date,
            submit_recipt,
        ])

    return response


@login_required(login_url='/crm/404/')
def admin_get_next_unique_code(prefix='EMTA'):
    candidate = Candidate_registration.objects.filter(unique_code__regex=r'^EC\d{6}$').values_list('unique_code', flat=True)
    numbers = [int(re.search(r'\d{6}', unique_code).group()) for unique_code in candidate]

    if numbers:
        next_number = max(numbers) + 1  
    else:
        next_number = 1 
    return f"EC{next_number:06d}"

@login_required(login_url='/crm/404/')
def vendor_bank_details(request, vendor_code):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    try:
        vendor = Vendor.objects.get(refer_code=vendor_code)
        bank_details = Vendor_bank_details.objects.get(vendor=vendor)
        candidate_count = Candidate.objects.filter(refer_code=vendor_code).count()
        
        context = {
            'vendor': vendor,
            'bank_details': bank_details,
            'candidate_count' : candidate_count
        }
        return render(request, 'crm/vendor_bank_details.html', context)
        
    except Vendor.DoesNotExist:
        return HttpResponse("Vendor not found", status=404)
    except Vendor_bank_details.DoesNotExist:
        return HttpResponse("Bank details not found for this vendor", status=404)
    

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
# from .models import Vendor, Candidate

@login_required(login_url='/crm/404/')
@require_POST
@csrf_exempt
def process_payment(request, vendor_code):
    try:
        # Verify user has permission to process payments
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({
                'success': False,
                'message': 'Permission denied'
            }, status=403)
        
        vendor = get_object_or_404(Vendor, refer_code=vendor_code)
        
        # Get all pending payments for this vendor
        pending_payments = Candidate.objects.filter(
            refer_code=vendor_code,
            vendor_commission_status='Pending',
            selection_status='Selected'
        )
        
        # Process each payment
        for candidate in pending_payments:
            # Your payment processing logic here
            candidate.vendor_commission_status = 'Paid'
            candidate.vendor_payout_date = timezone.now()
            candidate.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully processed {pending_payments.count()} payments',
            'payment_count': pending_payments.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)    

@login_required(login_url='/crm/404/')
def admin_evms_candidate_chat_list(request, candidate_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
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
        return redirect('admin_evms_candidate_chat_list', candidate_id=candidate_id)
    
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
    return render(request, 'crm/evms_candidate_chat_list.html', context)

@login_required(login_url='/crm/404/')
def admin_evms_delete_chat(request, pk):
    chat = get_object_or_404(EVMS_Candidate_chat, pk=pk)
    candidate_id = chat.candidate.id
    chat.delete()
    messages.success(request, 'Chat record deleted successfully!')
    return redirect('admin_evms_candidate_chat_list', candidate_id=candidate_id)

@login_required(login_url='/crm/404/')
def admin_evms_interview_list(request, candidate_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
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
            return redirect('admin_evms_interview_list', candidate_id=candidate_id)
        
        # Handle form submission
        interview_date_time = request.POST.get('interview_date_time')
        company_name = request.POST.get('company_name')
        job_position = request.POST.get('job_position')
        status = request.POST.get('status')
        interview_mode = request.POST.get('interview_mode')
        notes = request.POST.get('notes')
        
        interview = EVMS_Candidate_Interview(
            candidate=candidate,
            interview_date_time=interview_date_time,
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
        return redirect('admin_evms_interview_list', candidate_id=candidate_id)
    
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
    return render(request, 'crm/evms_candidate_interview_list.html', context)

@login_required(login_url='/crm/404/')
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

@login_required(login_url='/crm/404/')
def admin_evms_interview_detail(request, interview_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id)
    companys = Company_registration.objects.all()
    
    if request.method == 'POST':
        # Handle update
        interview.interview_date_time = request.POST.get('interview_date_time')
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
        return redirect('admin_evms_interview_detail', interview_id=interview.id)
    
    context = {
        'interview': interview,
        'status_choices': EVMS_Candidate_Interview.INTERVIEW_STATUS,
        'mode_choices': EVMS_Candidate_Interview.INTERVIEW_MODE,
        'companys' : companys
    }
    return render(request, 'crm/evms_candidate_interview_detail.html', context)

@login_required(login_url='/crm/404/')
def admin_evms_delete_interview(request, interview_id):
    interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id)
    candidate_id = interview.candidate.id
    interview.delete()
    messages.success(request, 'Interview deleted successfully!')
    return redirect('admin_evms_interview_list', candidate_id=candidate_id)


from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Subquery, OuterRef

def admin_invoice_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    candidates_reg = Candidate_registration.objects.filter(selection_status='Selected')
    candidates_can = Candidate.objects.filter(selection_status='Selected')
    candidates = list(chain(candidates_reg, candidates_can))
    
    # Handle None values in sorting by providing a default minimal date
    candidates.sort(key=lambda x: x.selection_date or date.min, reverse=True)
    
    context = {
        'candidates': candidates
    }
    return render(request, 'crm/admin-invoice-list.html', context)


def generate_candidate_invoice(request, candidate_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    try:
        candidate = Candidate_registration.objects.get(id=candidate_id, selection_status='Selected')
    except ObjectDoesNotExist:
        try:
            candidate = Candidate.objects.get(id=candidate_id, selection_status='Selected')
        except ObjectDoesNotExist:
            messages.error(request, 'Candidate not found or not selected.')
            return redirect('admin_invoice_list')

    # Try to fetch the matching company using the candidate's company_name
    company = None
    if candidate.company_name:
        try:
            company = Company_registration.objects.get(company_name__iexact=candidate.company_name.strip())
        except Company_registration.DoesNotExist:
            messages.warning(request, f"No company details found for: {candidate.company_name}")

    context = {
        'candidate': candidate,
        'company': company,  # Pass company to the template
    }

    return render(request, 'crm/candidate-invoice.html', context)


def selected_candidate_in_company(request, company_id):

    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    try:
        company = Company_registration.objects.get(id=company_id)
    except Company_registration.DoesNotExist:
        messages.error(request, 'Company not found.')
        return redirect('admin_invoice_list')

    candidates_reg = Candidate_registration.objects.filter(company_name=company.company_name, selection_status='Selected')
    candidates_can = Candidate.objects.filter(company_name=company.company_name, selection_status='Selected')
    candidates = list(chain(candidates_reg, candidates_can))
    
    # Handle None values in sorting by providing a default minimal date
    candidates.sort(key=lambda x: x.selection_date or date.min, reverse=True)
    
    context = {
        'company': company,
        'candidates': candidates
    }
    return render(request, 'crm/selected-candidate-in-company.html', context)

def bulk_candidate_invoice_generate(request, company_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    try:
        company = Company_registration.objects.get(id=company_id)
    except Company_registration.DoesNotExist:
        messages.error(request, 'Company not found.')
        return redirect('admin_invoice_list')

    candidates_reg = Candidate_registration.objects.filter(company_name=company.company_name, selection_status='Selected',invoice_status = 'Pending')
    candidates_can = Candidate.objects.filter(company_name=company.company_name, selection_status='Selected',invoice_status = 'Pending')
    candidates = list(chain(candidates_reg, candidates_can))
    
    # Handle None values in sorting by providing a default minimal date
    candidates.sort(key=lambda x: x.selection_date or date.min, reverse=True)
    
    context = {
        'company': company,
        'candidates': candidates
    }
    return render(request, 'crm/bulk-candidate-invoice-generate.html', context)

def generate_bulk_candidate_invoice(request, company_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    try:
        company = Company_registration.objects.get(id=company_id)
    except Company_registration.DoesNotExist:
        messages.error(request, 'Company not found.')
        return redirect('admin_invoice_list')

    candidates_reg = Candidate_registration.objects.filter(company_name=company.company_name, selection_status='Selected',invoice_status = 'Pending')
    candidates_can = Candidate.objects.filter(company_name=company.company_name, selection_status='Selected',invoice_status = 'Pending')
    candidates = list(chain(candidates_reg, candidates_can))
    
    # Handle None values in sorting by providing a default minimal date
    candidates.sort(key=lambda x: x.selection_date or date.min, reverse=True)
    
    context = {
        'company': company,
        'candidates': candidates
    }
    return render(request, 'crm/bulk-candidate-invoice-generate-page.html', context)


def admin_assign_candidate(request) :
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)

    candidates_reg = Candidate_registration.objects.filter(employee_assigned__isnull=False)
    candidates_can = Candidate.objects.filter(employee_assigned__isnull=False)
    candidates = list(chain(candidates_reg, candidates_can))
    candidates.sort(key=lambda x: x.selection_date or date.min, reverse=True)

    return render(request, 'crm/candidate-assignment.html', { 'candidates' : candidates })



import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta # Make sure to add this import
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Max, Q
from django.db.models.functions import TruncHour, TruncDate, TruncWeek, TruncMonth
from django.http import JsonResponse
from django.template.loader import render_to_string
# ===================================================================================
# == HELPER FUNCTION (Used by multiple views)
# ===================================================================================
# Make sure these imports are at the top of your views.py
import calendar
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncHour, TruncDate, TruncWeek, TruncMonth, Coalesce


# ===================================================================================
# == HELPER FUNCTION (Used by multiple views)
# ===================================================================================
def _get_chart_data(queryset, start_date, end_date, filter_q=None):
    if filter_q:
        queryset = queryset.filter(filter_q)

    chart_labels = []
    chart_data = []
    time_delta = end_date - start_date

    if time_delta.days < 1:
        data_by_time = queryset.annotate(hour=TruncHour('timestamp')).values('hour').annotate(count=Count('id')).order_by('hour')
        time_counts = {i: 0 for i in range(24)}
        for group in data_by_time: time_counts[group['hour'].hour] = group['count']
        chart_labels = [f"{hour}:00" for hour in time_counts.keys()]
        chart_data = list(time_counts.values())
    elif time_delta.days <= 14:
        data_by_time = queryset.annotate(date=TruncDate('timestamp')).values('date').annotate(count=Count('id')).order_by('date')
        time_counts = {start_date + timedelta(days=i): 0 for i in range((end_date - start_date).days + 1)}
        for group in data_by_time:
            if group['date'] in time_counts:
                time_counts[group['date']] = group['count']
        chart_labels = [day.strftime('%a, %b %d') for day in time_counts.keys()]
        chart_data = list(time_counts.values())
    elif time_delta.days <= 92:
        data_by_time = queryset.annotate(week=TruncWeek('timestamp')).values('week').annotate(count=Count('id')).order_by('week')
        time_counts = {}
        current_date = start_date - timedelta(days=start_date.weekday())
        while current_date <= end_date:
            time_counts[current_date] = 0
            current_date += timedelta(weeks=1)
        for group in data_by_time:
            if group['week'] in time_counts: time_counts[group['week']] = group['count']
        chart_labels = [week_start.strftime('Week of %b %d') for week_start in time_counts.keys()]
        chart_data = list(time_counts.values())
    else:
        data_by_time = queryset.annotate(month=TruncMonth('timestamp')).values('month').annotate(count=Count('id')).order_by('month')
        time_counts = {i: 0 for i in range(1, 13)}
        for group in data_by_time: time_counts[group['month'].month] = group['count']
        chart_labels = [calendar.month_name[i] for i in range(1, 13)]
        chart_data = list(time_counts.values())
    return chart_labels, chart_data


# ===================================================================================
@login_required(login_url='/crm/404/')
def admin_calls_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    
    period = request.GET.get('period', 'today')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_employee_ids = request.GET.getlist('employees') 
    
    today = timezone.now().date()
    if period == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = end_date = today
            period = 'today'
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        start_date = end_date = today
        period = 'today'

    all_employees = Employee.objects.all().order_by('first_name')
    employee_queryset = Employee.objects.all()
    
    apply_employee_filter = selected_employee_ids and 'all' not in selected_employee_ids
    if apply_employee_filter:
        employee_queryset = employee_queryset.filter(id__in=selected_employee_ids)

    base_activity_filter = Q(candidateactivity__timestamp__date__range=[start_date, end_date], candidateactivity__action__in=['call_made', 'created'], candidateactivity__employee__isnull=False)
    connected_filter = Q(Q(candidateactivity__action='call_made', candidateactivity__changes__call_connection__new__iexact='Connected') | Q(candidateactivity__action='created', candidateactivity__candidate__call_connection__iexact='Connected'))
    
    employee_stats = employee_queryset.annotate(
        total_calls=Count('candidateactivity', filter=base_activity_filter),
        last_call_made=Max('candidateactivity__timestamp', filter=base_activity_filter),
        connected_calls=Count('candidateactivity', filter=base_activity_filter & connected_filter),
        not_connected_calls=Count('candidateactivity', filter=base_activity_filter & ~connected_filter),
          ).filter(total_calls__gt=0).order_by('-total_calls')
    
    LEAD_STATUSES = ['Hot', 'Converted']
    lead_transition_filter = (Q(action='call_made', changes__lead_generate__new__in=LEAD_STATUSES) & ~Q(changes__lead_generate__old__in=LEAD_STATUSES)) | Q(action='created', candidate__lead_generate__in=LEAD_STATUSES)
    
    # --- START OF CHANGE ---
    for stat in employee_stats:
        employee_activities = CandidateActivity.objects.filter(employee=stat, timestamp__date__range=[start_date, end_date], action__in=['call_made', 'created', 'updated'])
        stat.leads_generated = employee_activities.filter(lead_transition_filter).annotate(date=TruncDate('timestamp')).values('candidate_id', 'date').distinct().count()
        stat.selections = Candidate_registration.objects.filter(updated_by=stat, selection_status__iexact='Selected', selection_date__range=[start_date, end_date]).count()
        
        # This now calculates a simple count instead of a percentage
        hot_to_converted_filter = Q(changes__lead_generate__new__iexact='Converted', changes__lead_generate__old__iexact='Hot')
        stat.converted_leads_count = employee_activities.filter(hot_to_converted_filter).count()
        # This now calculates a simple count of joined candidates for each employee
        stat.joined_count = Candidate_registration.objects.filter(
            updated_by=stat, 
            joining_status__iexact='Joined', 
            candidate_joining_date__range=[start_date, end_date]
        ).count()

        # === UPDATED RESUME LOGIC (INDIVIDUAL) ===
        # 1. New registrations with Resume
        created_resumes_count = Candidate_registration.objects.filter(
            created_by=stat,
            created_at__date__range=[start_date, end_date],
            candidate_resume__isnull=False
        ).exclude(candidate_resume='').count()

        # 2. Updated registrations with Resume (via Activity Log)
        updated_resumes_count = CandidateActivity.objects.filter(
            employee=stat,
            timestamp__date__range=[start_date, end_date],
            changes__has_key='candidate_resume'
        ).count()

        stat.resumes_added = created_resumes_count + updated_resumes_count

    all_activities_queryset = CandidateActivity.objects.filter(timestamp__date__range=[start_date, end_date], action__in=['call_made', 'created', 'updated'], employee__isnull=False)
    selections_queryset = Candidate_registration.objects.filter(selection_status__iexact='Selected', selection_date__range=[start_date, end_date])
    # New queryset for joined candidates
    joined_queryset = Candidate_registration.objects.filter(
        joining_status__iexact='Joined', 
        candidate_joining_date__range=[start_date, end_date]
    )
    
    # === UPDATED RESUME LOGIC (TOTAL QUERYSETS) ===
    resumes_created_qs = Candidate_registration.objects.filter(
        created_at__date__range=[start_date, end_date],
        candidate_resume__isnull=False
    ).exclude(candidate_resume='')
    
    resumes_updated_qs = CandidateActivity.objects.filter(
        timestamp__date__range=[start_date, end_date],
        changes__has_key='candidate_resume'
    )

    if apply_employee_filter:
        all_activities_queryset = all_activities_queryset.filter(employee_id__in=selected_employee_ids)
        selections_queryset = selections_queryset.filter(updated_by_id__in=selected_employee_ids)
        joined_queryset = joined_queryset.filter(updated_by_id__in=selected_employee_ids)
        
        # Apply filters to resume querysets
        resumes_created_qs = resumes_created_qs.filter(created_by_id__in=selected_employee_ids)
        resumes_updated_qs = resumes_updated_qs.filter(employee_id__in=selected_employee_ids)
        
    total_connected_filter = Q(Q(action='call_made', changes__call_connection__new__iexact='Connected') | Q(action='created', candidate__call_connection__iexact='Connected'))
    total_leads_generated_count = all_activities_queryset.filter(lead_transition_filter).annotate(date=TruncDate('timestamp')).values('candidate_id', 'date').distinct().count()
    total_selections_count = selections_queryset.count()
    total_joined_count = joined_queryset.count() # Get total joined count
    
    # Calculate Total Resumes (Sum of created + updated)
    total_resumes_count = resumes_created_qs.count() + resumes_updated_qs.count()
    
    total_hot_to_converted_filter = Q(changes__lead_generate__new__iexact='Converted', changes__lead_generate__old__iexact='Hot')
    
    total_stats_agg = all_activities_queryset.aggregate(
        total_activities=Count('id', filter=Q(action__in=['call_made', 'created'])),
        total_connected=Count('id', filter=total_connected_filter),
        total_not_connected=Count('id', filter=~total_connected_filter & Q(action__in=['call_made', 'created'])),
        # This new aggregation gets the total converted leads count
        total_converted_leads=Count('id', filter=total_hot_to_converted_filter)
        
    )
    
    total_stats = {
        **total_stats_agg, 
        'total_leads_generated': total_leads_generated_count, 
        'total_selections': total_selections_count,
        'total_joined': total_joined_count,
        'total_resumes_added': total_resumes_count
    }
    # --- END OF CHANGE ---

    unique_lead_activities = all_activities_queryset.filter(lead_transition_filter)
    unique_leads_dict = {}
    for activity in unique_lead_activities.order_by('timestamp'):
        unique_leads_dict[(activity.candidate_id, activity.timestamp.date())] = activity
    unique_leads_queryset = CandidateActivity.objects.filter(id__in=[act.id for act in unique_leads_dict.values()])
    
    main_chart_labels, main_chart_data = _get_chart_data(all_activities_queryset.filter(action__in=['call_made', 'created']), start_date, end_date)
    leads_chart_labels, leads_chart_data = _get_chart_data(unique_leads_queryset, start_date, end_date)
    
    interview_detail_qs = Candidate_Interview.objects.filter(interview_date_time__date__range=[start_date, end_date], status__in=['scheduled', 'rescheduled'])
    follow_up_candidates_qs = Candidate_registration.objects.filter(next_follow_up_date_time__date__range=[start_date, end_date])

    if apply_employee_filter:
        # Placeholder for your specific filter logic based on your models
        pass

    interview_detail = sorted(list(interview_detail_qs), key=lambda x: x.interview_date_time)
    follow_up_candidates = sorted(list(follow_up_candidates_qs), key=lambda x: x.next_follow_up_date_time)

    context = {
        'employee_stats': employee_stats, 'period': period, 'start_date': start_date, 'end_date': end_date,
        'main_chart_labels': main_chart_labels, 'main_chart_data': main_chart_data,
        'leads_chart_labels': leads_chart_labels, 'leads_chart_data': leads_chart_data,
        'total_stats': total_stats, 'interview_detail': interview_detail,
        'follow_up_candidates': follow_up_candidates, 
        'all_employees': all_employees,
        'selected_employee_ids': [int(eid) for eid in selected_employee_ids if eid.isdigit()],
    }
    return render(request, 'crm/employee-calls-list.html', context)

@login_required(login_url='/crm/404/')
def get_filtered_activity_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
        
    list_type = request.GET.get('list_type')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_employee_ids = request.GET.getlist('employees')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid date format."}, status=400)
    
    apply_employee_filter = selected_employee_ids and 'all' not in selected_employee_ids
    
    if list_type == 'selected':
        list_title = "Selected Candidates"
        candidates = Candidate_registration.objects.filter(
            selection_status__iexact='Selected', 
            selection_date__range=[start_date, end_date], 
            updated_by__isnull=False
        ).select_related('updated_by__user').order_by('-selection_date')
        if apply_employee_filter:
            candidates = candidates.filter(updated_by_id__in=selected_employee_ids)
        context = {'candidates': candidates, 'list_title': list_title}
        return render(request, 'crm/partials/selected_candidate_list_partial.html', context)

    activities = CandidateActivity.objects.filter(
        timestamp__date__range=[start_date, end_date], 
        action__in=['call_made', 'created', 'updated'], 
        employee__isnull=False
    ).select_related('employee__user', 'candidate')

    if apply_employee_filter:
        activities = activities.filter(employee_id__in=selected_employee_ids)

    list_title = "All Activities"
    LEAD_STATUSES = ['Hot', 'Converted']
    if list_type == 'leads':
        list_title = "Lead Generating Activities"
        leads_filter = (Q(action='call_made', changes__lead_generate__new__in=LEAD_STATUSES) & ~Q(changes__lead_generate__old__in=LEAD_STATUSES)) | Q(action='created', candidate__lead_generate__in=LEAD_STATUSES)
        activities = activities.filter(leads_filter)
        unique_leads = { (act.candidate_id, act.timestamp.date()): act for act in activities.order_by('timestamp') }
        activities = sorted(list(unique_leads.values()), key=lambda x: x.timestamp, reverse=True)
    elif list_type == 'connected':
        list_title = "Connected Activities"
        activities = activities.filter(Q(Q(action='call_made', changes__call_connection__new__iexact='Connected') | Q(action='created', candidate__call_connection__iexact='Connected')))
    elif list_type == 'not_connected':
        list_title = "Not Connected Activities"
        activities = activities.filter(~Q(Q(action='call_made', changes__call_connection__new__iexact='Connected') | Q(action='created', candidate__call_connection__iexact='Connected')))
    elif list_type == 'converted':
        list_title = "Hot to Converted Activities"
        activities = activities.filter(Q(changes__lead_generate__new__iexact='Converted', changes__lead_generate__old__iexact='Hot'))
    
    # --- START OF CHANGE ---
    elif list_type == 'joined':
        list_title = "Joined Candidates"
        candidates = Candidate_registration.objects.filter(
            joining_status__iexact='Joined', 
            candidate_joining_date__range=[start_date, end_date], 
            updated_by__isnull=False
        ).select_related('updated_by__user').order_by('-candidate_joining_date')
        if apply_employee_filter:
            candidates = candidates.filter(updated_by_id__in=selected_employee_ids)
        context = {'candidates': candidates, 'list_title': list_title}
        return render(request, 'crm/partials/joined_candidate_list_partial.html', context)
    
    elif list_type == 'resumes':
        list_title = "Candidates with Resumes Added/Updated"
        
        # 1. Candidates CREATED with a resume in the date range
        created_candidates_qs = Candidate_registration.objects.filter(
            created_at__date__range=[start_date, end_date],
            candidate_resume__isnull=False
        ).exclude(candidate_resume='')

        # 2. Candidates UPDATED with a resume in the date range (via Activity Log)
        updated_activities_qs = CandidateActivity.objects.filter(
            timestamp__date__range=[start_date, end_date],
            changes__has_key='candidate_resume'
        )

        # Apply Employee Filters separately to both queries
        if apply_employee_filter:
            created_candidates_qs = created_candidates_qs.filter(created_by_id__in=selected_employee_ids)
            updated_activities_qs = updated_activities_qs.filter(employee_id__in=selected_employee_ids)

        # Combine IDs from both sources
        created_ids = list(created_candidates_qs.values_list('id', flat=True))
        updated_ids = list(updated_activities_qs.values_list('candidate_id', flat=True))
        all_candidate_ids = list(set(created_ids + updated_ids))

        # Fetch the final list of Candidate objects
        candidates = Candidate_registration.objects.filter(
            id__in=all_candidate_ids
        ).select_related('created_by__user').order_by('-updated_at')
        
        context = {'candidates': candidates, 'list_title': list_title}
        return render(request, 'crm/partials/resume_list_partial.html', context)
    
    else: # 'total'
        activities = activities.filter(action__in=['call_made', 'created']).order_by('-timestamp')
    
    context = {'activities': activities, 'list_title': list_title}
    return render(request, 'crm/partials/activity_list_partial.html', context)


# ... (keep all your existing imports and other views) ...

@login_required(login_url='/crm/404/')
def get_employee_candidates(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
        
    employee_id = request.GET.get('employee_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not all([employee_id, start_date_str, end_date_str]):
        return JsonResponse({"error": "Missing parameters."}, status=400)
        
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        employee = get_object_or_404(Employee, pk=employee_id)
        
        employee_activities_queryset = CandidateActivity.objects.filter(
            employee=employee, timestamp__date__range=[start_date, end_date],
            action__in=['call_made', 'created']
        ).select_related('candidate').order_by('-timestamp')

        # --- START OF FIX: Add a manual counter ---
        activities_for_template = []
        activities_list = list(employee_activities_queryset)
        
        activity_counter = 1 # Initialize a manual counter
        
        for i, activity in enumerate(activities_list):
            # Add the activity with its correct serial number
            activities_for_template.append({
                'type': 'activity',
                'data': activity,
                's_no': activity_counter # Add the serial number here
            })
            activity_counter += 1 # Increment the counter ONLY for activities

            # Check for a time gap between this activity and the next (older) one
            if i + 1 < len(activities_list):
                next_activity = activities_list[i+1]
                time_difference = activity.timestamp - next_activity.timestamp
                
                if time_difference > timedelta(minutes=15):
                    hours, remainder = divmod(time_difference.total_seconds(), 3600)
                    minutes, _ = divmod(remainder, 60)
                    hours, minutes = int(hours), int(minutes)
                    
                    duration_str = "Gap of "
                    if hours > 0:
                        duration_str += f"{hours}h "
                    if minutes > 0 or hours == 0:
                        duration_str += f"{minutes}m"
                    
                    activities_for_template.append({
                        'type': 'gap',
                        'duration': duration_str.strip()
                    })
        # --- END OF FIX ---
        
        html_content = render_to_string(
            'crm/partials/candidate_list_partial.html',
            # Use the newly created list for the template context
            {'processed_activities': activities_for_template, 'employee': employee}
        )
        
        # NOTE: The chart and lead calculations below remain the same
        activity_chart_labels, activity_chart_data = _get_chart_data(employee_activities_queryset, start_date, end_date)
        
        LEAD_STATUSES = ['Hot', 'Converted']
        leads_filter_q = (Q(action='call_made', changes__lead_generate__new__in=LEAD_STATUSES) & ~Q(changes__lead_generate__old__in=LEAD_STATUSES)) | Q(action='created', candidate__lead_generate__in=LEAD_STATUSES)
        employee_lead_transitions = employee_activities_queryset.filter(leads_filter_q)
        
        unique_employee_leads_dict = {}
        for activity in employee_lead_transitions.order_by('timestamp'):
            unique_employee_leads_dict[(activity.candidate_id, activity.timestamp.date())] = activity
        unique_employee_leads_qs = CandidateActivity.objects.filter(id__in=[act.id for act in unique_employee_leads_dict.values()])
        
        leads_chart_labels, leads_chart_data = _get_chart_data(unique_employee_leads_qs, start_date, end_date)
        
        return JsonResponse({
            'html': html_content,
            'activity_chart_data': {'labels': activity_chart_labels, 'data': activity_chart_data,},
            'leads_chart_data': {'labels': leads_chart_labels, 'data': leads_chart_data,}
        })

    except (ValueError, Employee.DoesNotExist):
        return JsonResponse({"error": "Invalid request."}, status=400)

        
            
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from CRM.models import *
from django.utils import timezone

@login_required(login_url='/crm/404/')
def admin_task_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    """
    Admin/Manager view:
    - Displays a form to create new tasks.
    - Lists all tasks in the system.
    - Handles form submission without forms.py.
    """
    current_employee = get_object_or_404(Employee, user=request.user)

    if request.method == 'POST':
        # --- Manual Form Processing ---
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date') or None
        candidate_id = request.POST.get('candidate')
        assignee_ids = request.POST.getlist('assigned_to')

        # Create the task object
        new_task = Task.objects.create(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            assigned_by=current_employee
        )

        # Link candidate if provided
        if candidate_id:
            new_task.candidate = get_object_or_404(Candidate_registration, pk=candidate_id)
        
        # Add assignees
        if assignee_ids:
            assignees = Employee.objects.filter(id__in=assignee_ids)
            new_task.assigned_to.set(assignees)
        
        new_task.save()

        # Handle file attachments
        for f in request.FILES.getlist('attachments'):
            TaskAttachment.objects.create(
                task=new_task,
                file=f,
                uploaded_by=current_employee
            )
        
        # Create history record for task creation
        TaskHistory.objects.create(
            task=new_task,
            employee=current_employee,
            action='CREATED',
            details=f"Task was created and assigned to: {', '.join([f'{emp.first_name} {emp.last_name}' for emp in new_task.assigned_to.all()])}."
        )
            
        return redirect('admin_task_dashboard')

    # --- For GET request ---
    all_tasks = Task.objects.all().prefetch_related('assigned_to', 'attachments')
    all_employees = Employee.objects.all()
    all_candidates = Candidate_registration.objects.all()
    
    context = {
        'tasks': all_tasks,
        'all_employees': all_employees,
        'all_candidates': all_candidates,
    }
    return render(request, 'crm/admin_dashboard.html', context)


@login_required(login_url='/crm/404/')
def admin_task_detail_and_reassign(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    """
    Employee/Admin view:
    - Shows details of a specific task and its history.
    - Allows re-assigning and updating the task status/priority.
    """
    task = get_object_or_404(Task, pk=pk)
    current_employee = get_object_or_404(Employee, user=request.user)

    if request.method == 'POST':
        # --- Manual Update Processing ---
        
        # 1. Handle Re-assignment
        new_assignee_ids = set(request.POST.getlist('assigned_to'))
        current_assignee_ids = set(task.assigned_to.values_list('id', flat=True))
        
        if new_assignee_ids != current_assignee_ids:
            new_assignees = Employee.objects.filter(id__in=new_assignee_ids)
            task.assigned_to.set(new_assignees)
            TaskHistory.objects.create(
                task=task,
                employee=current_employee,
                action='REASSIGNED',
                details=f"Assignees updated to: {', '.join([emp.first_name for emp in new_assignees])}."
            )

        # 2. Handle Status Change
        new_status = request.POST.get('status')
        if new_status and new_status != task.status:
            old_status = task.get_status_display()
            task.status = new_status
            task.save()
            TaskHistory.objects.create(
                task=task,
                employee=current_employee,
                action='STATUS_CHANGED',
                details=f"Status changed from '{old_status}' to '{task.get_status_display()}'."
            )

        # 3. Handle Priority Change
        new_priority = request.POST.get('priority')
        if new_priority and new_priority != task.priority:
            old_priority = task.get_priority_display()
            task.priority = new_priority
            task.save()
            TaskHistory.objects.create(
                task=task,
                employee=current_employee,
                action='PRIORITY_CHANGED',
                details=f"Priority changed from '{old_priority}' to '{task.get_priority_display()}'."
            )

        return redirect('admin_task_detail_and_reassign', pk=task.pk)

    all_employees = Employee.objects.all()
    task_history = TaskHistory.objects.filter(task=task)
    context = {
        'task': task,
        'all_employees': all_employees,
        'history': task_history,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }
    return render(request, 'crm/task_detail.html', context)


def is_admin_or_staff(user):
    """Check if the user is a superuser or staff member."""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(is_admin_or_staff)
def bulk_assign_candidates(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'crm/404.html', status=404)
    """
    A view for administrators and staff to bulk-assign unassigned candidates 
    to a specific employee.
    """
    if request.method == 'POST':
        candidate_ids = request.POST.getlist('candidate_ids')
        employee_id = request.POST.get('employee_id')

        if not candidate_ids:
            messages.error(request, "Please select at least one candidate to assign.")
            return redirect('bulk_assign_candidates')

        if not employee_id:
            messages.error(request, "Please select an employee to assign the candidates to.")
            return redirect('bulk_assign_candidates')

        try:
            # Find the employee to assign the candidates to
            assign_to_employee = Employee.objects.get(pk=employee_id)
            
            # Efficiently update all selected candidates in a single database query
            candidates_to_assign = Candidate_registration.objects.filter(pk__in=candidate_ids)
            updated_count = candidates_to_assign.update(assigned_to=assign_to_employee)

            messages.success(
                request, 
                f"Successfully assigned {updated_count} candidates to {assign_to_employee}."
            )

        except Employee.DoesNotExist:
            messages.error(request, "The selected employee could not be found.")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            
        return redirect('bulk_assign_candidates')

    # For GET requests, display the page
    # We fetch only unassigned candidates to keep the list clean
    unassigned_candidates = Candidate_registration.objects.filter(assigned_to__isnull=True)
    all_employees = Employee.objects.all()

    context = {
        'candidates': unassigned_candidates,
        'employees': all_employees,
    }
    return render(request, 'crm/bulk_assign_candidates.html', context)


@login_required
def emta_co_in_course_application_view(request):
    inquiries = CourseInquiry.objects.all()
    context = {
        'inquiries': inquiries
    }
    return render(request, 'crm/emta_co_in_course_application.html', context)

@login_required
def emta_co_in_job_application_view(request):
    applications = JobApplication.objects.all()
    context = {
        'applications': applications
    }
    return render(request, 'crm/emta_co_in_jobs_application.html', context)

@login_required
def emta_co_in_contact_queries_view(request):
    queries = ContactQuery.objects.all()
    context = {
        'queries': queries
    }
    return render(request, 'crm/emta_co_in_contact_queries.html', context)

@login_required
def delete_course_inquiry(request, id):
    # Only allow POST requests for deletion
    if request.method == 'POST':
        inquiry = get_object_or_404(CourseInquiry, id=id)
        inquiry.delete()

        messages.success(request, "Course inquiry deleted successfully.")
    # Redirect back to the list view, whether it was POST or not
    return redirect('emta_co_in_course_application_view') # Use the name from your urls.py

@login_required
def delete_job_application(request, id):
    if request.method == 'POST':
        application = get_object_or_404(JobApplication, id=id)
        application.delete()
        messages.success(request, "Job application deleted successfully.")
    return redirect('emta_co_in_job_application_view') # Use the name from your urls.py

@login_required
def delete_contact_query(request, id):
    if request.method == 'POST':
        query = get_object_or_404(ContactQuery, id=id)
        query.delete()
        messages.success(request, "Contact query deleted successfully.")
    return redirect('emta_co_in_contact_queries_view') # Use the name from your urls.py

@login_required
def banking_counselling_view(request):
    candidates = Candidate_registration.objects.filter(
    calling_remark__in=[
        "Shortlisted for Banking Counselling",
        "Not Interested in BFSI Training",
        "Not Interested in BFSI Jobs",
        "Not Interested Due to Training Duration",
        "Not Interested Due to Training Fee",
        "Not Eligible Due to CIBIL Score",
        "Not Eligible Due to Education Issue",
    ]
)

    context = {
        'candidates': candidates
    }
    return render(request, 'crm/banking_counselling.html', context)


@login_required(login_url='/crm/404/')
def admin_bfsi_candidate_registration(request):
    logged_in_employee = Employee.objects.get(user=request.user)
    
    if request.method == 'POST':
        candidate_mobile_number = request.POST.get('candidate_mobile_number')
        
        # Check for duplicates by mobile number
        try:
            duplicate_candidate = Candidate_registration.objects.get(
                candidate_mobile_number=candidate_mobile_number
            )
            # If a duplicate is found, return a JSON response with the candidate's details
            return JsonResponse({
                'status': 'duplicate',
                'message': 'Mobile number already registered.',
                'candidate_id': duplicate_candidate.id,
                'candidate_name': duplicate_candidate.candidate_name,
                'candidate_profile_url': reverse('admin_candidate_profile', args=[duplicate_candidate.id])
            }, status=409)  # Use status code 409 for Conflict
        except Candidate_registration.DoesNotExist:
            pass # No duplicate found, continue with registration

        # Process the form data
        candidate_name = request.POST.get('candidate_name')
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
        next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None
        remark = request.POST.get('remark')
        submit_by = request.POST.get('submit_by')
        preferred_location_str = ', '.join(preferred_location)
        sector_str = ', '.join(sector)
        department_str = ', '.join(department)
        other_lead_source = request.POST.get('other_lead_source')
        other_qualification = request.POST.get('other_qualification')
        other_origin_location = request.POST.get('other_origin_location')
        other_preferred_location = request.POST.get('other_preferred_location')
        other_sector = request.POST.get('other_sector')
        other_department = request.POST.get('other_department')
        current_salary_type = request.POST.get('current_salary_type')
        expected_salary_type = request.POST.get('expected_salary_type')
        bfsi_batch_date = request.POST.get('bfsi_batch_date')
        bfsi_payment_status = request.POST.get('bfsi_payment_status')
        bfsi_payment_date = request.POST.get('bfsi_payment_date')
        bfsi_payment_remark = request.POST.get('bfsi_payment_remark')
        bfsi_payment_attachment = request.FILES.get('bfsi_payment_attachment')
        bfsi_candidature_status = request.POST.get('bfsi_candidature_status')
        
        # Save to database
        candidate = Candidate_registration.objects.create(
            employee_name=logged_in_employee,
            candidate_name=candidate_name,
            candidate_mobile_number=candidate_mobile_number,
            candidate_alternate_mobile_number=candidate_alternate_mobile_number,
            candidate_email_address=candidate_email_address,
            gender=gender,
            lead_source=lead_source,
            preferred_location=preferred_location_str,
            origin_location=origin_location,
            qualification=qualification,
            diploma=diploma,
            sector=sector_str,
            department=department_str,
            experience_year=experience_year,
            experience_month=experience_month,
            current_company=current_company,
            current_working_status=current_working_status,
            current_salary=current_salary,
            expected_salary=expected_salary,
            call_connection=call_connection,
            calling_remark=calling_remark,
            lead_generate=lead_generate,
            send_for_interview=send_for_interview,
            next_follow_up_date_time=next_follow_up_date_time,
            candidate_photo=candidate_photo,
            candidate_resume=candidate_resume,
            remark=remark,
            submit_by=submit_by,
            other_lead_source=other_lead_source,
            other_qualification=other_qualification,
            other_origin_location=other_origin_location,
            other_preferred_location=other_preferred_location,
            other_sector=other_sector,
            other_department=other_department,
            current_salary_type=current_salary_type,
            expected_salary_type=expected_salary_type,
            bfsi_batch_date=bfsi_batch_date,
            bfsi_payment_status=bfsi_payment_status,
            bfsi_payment_date=bfsi_payment_date,
            bfsi_payment_remark=bfsi_payment_remark,
            bfsi_payment_attachment=bfsi_payment_attachment,
            bfsi_candidature_status=bfsi_candidature_status
        )

        # Create a CandidateActivity record
        CandidateActivity.objects.create(
            candidate=candidate,
            employee=logged_in_employee,
            action='created',
            # changes=changes,
            remark="Created via unified form"
        )

        return JsonResponse({'status': 'success', 'redirect_url': reverse('banking_counselling_view')})
    else:
        # suggested_unique_code = get_next_unique_code()

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
            "Ujjain", "Umaria", "Vidisha","Anantapur", "Chittoor", "East Godavari", "Guntur", "Krishna", "Kurnool", "Nellore", "Prakasam", "Srikakulam", "Visakhapatnam", "Vizianagaram", "West Godavari",
            "Anjaw", "Changlang", "Dibang Valley", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang", "East Siang",
            "Barpeta", "Bongaigaon", "Cachar", "Charaideo", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Dima Hasao", "Goalpara", "Golaghat", "Hailakandi", "Hazaribag", "Jorhat", "Kamrup Metropolitan", "Kamrup", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Majuli", "Moranha", "Nagaon", "Nalbari", "North Cachar Hills", "Sivasagar", "Sonitpur", "South Cachar Hills", "Tinsukia", "Udalguri", "West Karbi Anglong",
            "Araria", "Aurangabad", "Bhojpur", "Buxar", "Darbhanga", "East Champaran", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali", "West Champaran",
            "Balod", "Baloda Bazar", "Balrampur", "Bastar", "Bemetara", "Bijapur", "Bilaspur", "Dakshin Bastar Dantewada", "Dhamtari", "Durg", "Gariyaband", "Gaurela Pendra Marwahi", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Koriya", "Mahasamund", "Mungeli", "Narayanpur",
            "North Goa", "South Goa","Ahmedabad", "Amreli", "Anand", "Aravalli", "Banaskantha", "Bharuch", "Bhavnagar", "Botad", "Chhota Udaipur", "Dahod", "Dang", "Devbhoomi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Kutch", "Mahisagar", "Mehsana", "Morbi", "Narmada", "Navsari", "Panchmahal", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad",
            "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar",
            "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kinnaur", "Kullu", "Lahaul and Spiti", "Mandi", "Shimla", "Sirmaur", "Solan", "Una",
            "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "East Singhbhum", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribagh", "Jamtara", "Khunti", "Koderma", "Latehar", "Lohardaga", "Pakur", "Palamu", "Ramgarh", "Ranchi", "Sahebganj", "Seraikela Kharsawan", "Simdega", "West Singhbhum",
            "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban", "Bidar", "Chamarajanagar", "Chikballapur", "Chikkamagaluru", "Chitradurga", "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri", "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur", "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada", "Vijayapura", "Yadgir",
            "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad",
            "Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal",
            "Bishnupur", "Chandel", "Churachandpur", "Imphal East", "Imphal West", "Jiribam", "Kakching", "Kamjong", "Kangpokpi", "Noney", "Pherzawl", "Senapati", "Tamenglong", "Tengnoupal", "Thoubal", "Ukhrul",
            "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "North Garo Hills", "Ri Bhoi", "South Garo Hills", "South West Garo Hills", "South West Khasi Hills", "West Garo Hills", "West Jaintia Hills", "West Khasi Hills",
            "Aizawl", "Champhai", "Hnahthial", "Khawzawl", "Kolasib", "Lawngtlai", "Lunglei", "Mamit", "Saiha", "Saitual", "Serchhip",
            "Dimapur", "Kiphire", "Kohima", "Longleng", "Mokokchung", "Mon", "Peren", "Phek", "Tuensang", "Wokha", "Zunheboto",
            "Angul", "Balangir", "Balasore", "Bargarh", "Bhadrak", "Bhubaneswar", "Boudh", "Cuttack", "Deogarh", "Dhenkanal", "Gajapati", "Ganjam", "Jagatsinghpur", "Jajpur", "Jharsuguda", "Kalahandi", "Kandhamal", "Kendrapara", "Kendujhar", "Khordha", "Koraput", "Malkangiri", "Mayurbhanj", "Nabarangpur", "Nayagarh", "Nuapada", "Puri", "Rayagada", "Sambalpur", "Subarnapur", "Sundargarh",
            "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Ferozepur", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Muktsar", "Nawanshahr", "Pathankot", "Patiala", "Rupnagar", "Sangrur", "SAS Nagar", "Tarn Taran",
            "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
            "East Sikkim", "North Sikkim", "South Sikkim", "West Sikkim",
            "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanchipuram", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", "Virudhunagar",
            "Adilabad", "Bhadradri Kothagudem", "Hyderabad", "Jagtial", "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy", "Karimnagar", "Khammam", "Komaram Bheem Asifabad", "Mahabubabad", "Mahabubnagar", "Mancherial", "Medak", "Medchal-Malkajgiri", "Mulugu", "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad", "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy", "Warangal Rural", "Warangal Urban", "Yadadri Bhuvanagiri",
            "Dhalai", "Gomati", "Khowai", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura",
            "Agra", "Aligarh", "Ambedkar Nagar", "Amethi", "Amroha", "Auraiya", "Azamgarh", "Baghpat", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Bulandshahr", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Ayodhya", "Farrukhabad", "Fatehpur", "Firozabad", "Gautam Buddha Nagar", "Ghaziabad", "Ghazipur", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kannauj", "Kanpur Dehat", "Kanpur Nagar", "Kasganj", "Kaushambi", "Kushinagar", "Lakhimpur Kheri", "Lalitpur", "Lucknow", "Maharajganj", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Prayagraj", "Rae Bareli", "Rampur", "Saharanpur", "Sambhal", "Sant Kabir Nagar", "Shahjahanpur", "Shamli", "Shravasti", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi",
            "Almora", "Bageshwar", "Chamoli", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Pithoragarh", "Rudraprayag", "Tehri Garhwal", "Udham Singh Nagar", "Uttarkashi",
            "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur", "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia", "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur",
            "Nicobar", "North and Middle Andaman", "South Andaman", "Chandigarh", "Dadra and Nagar Haveli", "Daman", "Diu", "Central Delhi", "East Delhi", "New Delhi", "North Delhi", "North East Delhi", "North West Delhi", "Shahdara", "South Delhi", "South East Delhi", "South West Delhi", "West Delhi",
            "Anantnag", "Bandipora", "Baramulla", "Budgam", "Doda", "Ganderbal", "Jammu", "Kathua", "Kishtwar", "Kulgam", "Kupwara", "Poonch", "Pulwama", "Rajouri", "Ramban", "Reasi", "Samba", "Shopian", "Srinagar", "Udhampur",
            "Kargil", "Leh", "Lakshadweep", "Karaikal", "Mahe", "Puducherry", "Yanam"

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
            # 'suggested_unique_code':suggested_unique_code,
            'districts' : districts,
            'job_sectors' : job_sectors,
            'departments' : departments,
            'state' : state,
            'state_distict' : state_distict
        }
        return render (request,'crm/bfsi-candidate-registration.html',context)
   

@login_required(login_url='/employee/404/')
@require_POST
def check_mobile_number_duplicate_bfsi(request):
    """
    Checks if a mobile number already exists and returns details for the modal.
    """
    try:
        data = json.loads(request.body)
        mobile_number = data.get('mobile_number')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    if mobile_number:
        try:
            duplicate_candidate = Candidate_registration.objects.get(
                candidate_mobile_number=mobile_number
            )
            # If a candidate is found, return all data needed for the modal
            return JsonResponse({
                'status': 'duplicate',
                'candidate_name': duplicate_candidate.candidate_name,
                # ADD THIS LINE to provide the URL for the button
                'candidate_profile_url': reverse('admin_candidate_profile', args=[duplicate_candidate.id])
            }, status=409)
        except Candidate_registration.DoesNotExist:
            # If no candidate is found, return a success status
            return JsonResponse({'status': 'unique'}, status=200)

    return JsonResponse({'error': 'Mobile number is required'}, status=400)



@login_required(login_url='/crm/404/')
def interview_schedule_list(request):
    """
    Displays a list of all scheduled interviews with filters.
    """
    # Use select_related to optimize the query by fetching related objects in a single DB hit
    interviews_qs = Candidate_Interview.objects.select_related(
        'candidate', 
        'created_by'
    ).all()

    # Get a list of employees who have scheduled interviews to populate the filter
    employee_ids = interviews_qs.exclude(created_by__isnull=True)\
                                .values_list('created_by_id', flat=True)\
                                .distinct()
    employees = Employee.objects.all()

    # Get all possible statuses directly from the model choices
    interview_statuses = Candidate_Interview.INTERVIEW_STATUS

    context = {
        'interviews': interviews_qs,
        'employees': employees,
        'interview_statuses': interview_statuses,
        # The company and job position filters will be populated dynamically via JavaScript
        # from the data present in the table for simplicity, as per your provided template.
    }
    return render(request, 'crm/interview_schedule_list.html', context)

from django.contrib.humanize.templatetags.humanize import naturaltime

@login_required
def notification_history(request):
    all_notifications = Notification.objects.filter(recipient=request.user)
    context = {'all_notifications': all_notifications}
    return render(request, 'crm/notification_history.html', context)

@login_required
def mark_all_as_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    if notification.candidate and notification.candidate.id:
        # IMPORTANT: Make sure your candidate detail URL is named 'admin_candidate_profile'
        return redirect('admin_candidate_profile', id=notification.candidate.id) 
    return redirect('notification_history')

@login_required
def get_unread_notifications_api(request):
    notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).select_related('candidate').values(
        'id', 
        'message', 
        'created_at',
        'notification_type',
        'candidate__candidate_name'
    ).order_by('-created_at')

    notifications_list = list(notifications)
    for notif in notifications_list:
        notif['timesince'] = naturaltime(notif['created_at'])

    return JsonResponse({
        'notifications': notifications_list,
        'unread_count': len(notifications_list)
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta, datetime, date
from django.db.models import Count, Max, Q
from django.db.models.functions import TruncDate
# from .models import Employee, CandidateActivity, Candidate_registration
from collections import Counter
from django.contrib.auth.decorators import login_required


@login_required
def employee_daily_report(request):
    """
    Shows a day-by-day performance breakdown for a single employee
    and allows filtering by employee and date.
    """
    today = timezone.now().date()
    
    # --- Read filters from GET parameters ---
    period = request.GET.get('period', 'week') 
    employee_id = request.GET.get('employee')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not employee_id:
        # Redirect to the main dashboard if no employee is specified in the URL
        return redirect('admin_calls_list')

    # --- Determine date range from filters ---
    if period == 'custom' and start_date_str and end_date_str:
        start_date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    elif period == 'week':
        start_date_obj = today - timedelta(days=today.weekday())
        end_date_obj = start_date_obj + timedelta(days=6)
    elif period == 'month':
        start_date_obj = today.replace(day=1)
        end_date_obj = (start_date_obj.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    elif period == 'year':
        start_date_obj = today.replace(month=1, day=1)
        end_date_obj = today.replace(month=12, day=31)
    else: # Default to today
        start_date_obj = end_date_obj = today
        period = 'today'

    employee = get_object_or_404(Employee, pk=employee_id)
    all_employees = Employee.objects.all().order_by('first_name')
    
    # --- Fetch and process data ---
    
    # 1. General Activities for Calls and Leads logic
    activities = list(CandidateActivity.objects.filter(
        employee=employee, 
        timestamp__date__range=[start_date_obj, end_date_obj], 
        action__in=['call_made', 'created', 'updated']
    ))

    # 2. RESUME LOGIC (COMBINED)
    # A. Get dates where NEW candidates were created with a resume
    created_resume_dates = list(Candidate_registration.objects.filter(
        created_by=employee, 
        created_at__date__range=[start_date_obj, end_date_obj], 
        candidate_resume__isnull=False
    ).exclude(candidate_resume='').values_list('created_at__date', flat=True))

    # B. Get dates where EXISTING candidates had a resume updated/added
    # We look for the 'candidate_resume' key in the changes JSON
    updated_resume_dates = list(CandidateActivity.objects.filter(
        employee=employee,
        timestamp__date__range=[start_date_obj, end_date_obj],
        changes__has_key='candidate_resume'
    ).values_list('timestamp__date', flat=True))

    # C. Combine both lists and Count
    all_resume_dates = created_resume_dates + updated_resume_dates
    resume_counts = Counter(all_resume_dates)

    # 3. Selection and Joining Logic
    selection_dates = list(Candidate_registration.objects.filter(updated_by=employee, selection_status__iexact='Selected', selection_date__range=[start_date_obj, end_date_obj]).values_list('selection_date', flat=True))
    joined_dates = list(Candidate_registration.objects.filter(updated_by=employee, joining_status__iexact='Joined', candidate_joining_date__range=[start_date_obj, end_date_obj]).values_list('candidate_joining_date', flat=True))
    
    selection_counts = Counter(selection_dates)
    joined_counts = Counter(joined_dates)

    # --- Build Daily Data ---
    daily_performance_data = []
    current_date = start_date_obj
    
    while current_date <= end_date_obj:
        day_activities = [act for act in activities if act.timestamp.date() == current_date]
        
        # Calculate Calls
        total_calls = sum(1 for act in day_activities if act.action in ['call_made', 'created'])
        connected_calls = sum(1 for act in day_activities if ((act.action == 'call_made' and act.changes.get('call_connection', {}).get('new') == 'Connected') or (act.action == 'created' and hasattr(act, 'candidate') and act.candidate.call_connection == 'Connected')))
        
        # Calculate Leads
        LEAD_STATUSES = ['Hot', 'Converted']
        leads_generated = len({act.candidate_id for act in day_activities if ((act.action == 'call_made' and act.changes.get('lead_generate', {}).get('new') in LEAD_STATUSES and act.changes.get('lead_generate', {}).get('old') not in LEAD_STATUSES) or (act.action == 'created' and hasattr(act, 'candidate') and act.candidate.lead_generate in LEAD_STATUSES))})
        converted_leads = len({act.candidate_id for act in day_activities if (act.action == 'call_made' and act.changes.get('lead_generate', {}).get('new') == 'Converted' and act.changes.get('lead_generate', {}).get('old') == 'Hot')})
        
        last_activity_time = max(act.timestamp for act in day_activities) if day_activities else None

        daily_performance_data.append({
            'date': current_date, 
            'total_calls': total_calls, 
            'connected_calls': connected_calls,
            'not_connected_calls': total_calls - connected_calls, 
            'resumes_added': resume_counts.get(current_date, 0), # This now includes Created + Updated
            'leads_generated': leads_generated, 
            'converted_leads': converted_leads,
            'selections': selection_counts.get(current_date, 0), 
            'joined': joined_counts.get(current_date, 0),
            'last_activity_time': last_activity_time,
        })
        current_date += timedelta(days=1)
        
    context = {
        'employee': employee,
        'all_employees': all_employees,
        'daily_performance': daily_performance_data,
        'start_date': start_date_obj,
        'end_date': end_date_obj,
        'period': period,
        'selected_employee_id': int(employee_id),
    }
    
    return render(request, 'crm/employee_daily_report.html', context)

# ... (keep all your existing imports and other views) ...

@login_required
def get_daily_activities_ajax(request):
    """
    This AJAX view fetches the activities for a specific employee on a single day.
    """
    employee_id = request.GET.get('employee_id')
    activity_date_str = request.GET.get('activity_date')

    try:
        employee = get_object_or_404(Employee, pk=employee_id)
        activity_date = datetime.strptime(activity_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    daily_activities = CandidateActivity.objects.filter(
        employee=employee,
        timestamp__date=activity_date,
        action__in=['call_made', 'created']
    ).select_related('candidate').order_by('-timestamp')

    # --- START OF FIX ---
    # Process activities to find time gaps and add a correct serial number
    activities_for_template = []
    activities_list = list(daily_activities)
    
    activity_counter = 1 # Initialize a manual counter
    
    for i, activity in enumerate(activities_list):
        # Add the activity with its correct serial number
        activities_for_template.append({
            'type': 'activity', 
            'data': activity,
            's_no': activity_counter # Add the serial number here
        })
        activity_counter += 1 # Increment the counter ONLY for activities

        # Check for a time gap between this activity and the next one
        if i + 1 < len(activities_list):
            next_activity = activities_list[i+1]
            time_difference = activity.timestamp - next_activity.timestamp
            if time_difference > timedelta(minutes=15):
                hours, remainder = divmod(time_difference.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                duration_str = f"Gap of {int(hours)}h {int(minutes)}m" if int(hours) > 0 else f"Gap of {int(minutes)}m"
                activities_for_template.append({'type': 'gap', 'duration': duration_str.strip()})
    # --- END OF FIX ---

    html = render_to_string(
        'crm/partials/daily_activity_details.html',
        {'processed_activities': activities_for_template}
    )
    return JsonResponse({'html': html})


from Employee.attendance_utils import calculate_daily_attendance 
import datetime as ed

def is_admin_or_manager(user):
    # Implement your logic to check if user is admin/manager
    # For now, we'll just check for staff status
    return user.is_staff 

@user_passes_test(is_admin_or_manager)
def admin_attendance_report(request):
    
    # Get filters from query params
    selected_user_id = request.GET.get('employee_id')
    end_date_str = request.GET.get('end_date', timezone.now().strftime('%Y-%m-%d'))
    start_date_str = request.GET.get('start_date', (timezone.now() - ed.timedelta(days=7)).strftime('%Y-%m-%d'))
    
    end_date = parse_date(end_date_str)
    start_date = parse_date(start_date_str)

    # Get all users who are employees for the dropdown
    all_employees = User.objects.filter(employee__isnull=False).select_related('employee')
    
    # Base query
    all_punches_query = AttendancePunch.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).select_related('user', 'user__employee').order_by('user', 'timestamp') # Order ASC for grouping

    if selected_user_id:
        all_punches_query = all_punches_query.filter(user__id=selected_user_id)
        
    # Group punches by user, then by day
    punches_by_user_day = {}
    for punch in all_punches_query:
        user = punch.user
        date = punch.timestamp.date()
        if user.id not in punches_by_user_day:
            punches_by_user_day[user.id] = {'user': user, 'days': {}}
        if date not in punches_by_user_day[user.id]['days']:
            punches_by_user_day[user.id]['days'][date] = []
        punches_by_user_day[user.id]['days'][date].append(punch)

    # Calculate stats
    report_data = []
    
    # Determine which users to iterate over
    users_to_process = all_employees
    if selected_user_id:
        users_to_process = all_employees.filter(id=selected_user_id)

    # We need this hack again for the utility function
    class PunchList:
        def __init__(self, punches):
            self._punches = punches
        def all(self):
            return self._punches
        def __bool__(self):
            return bool(self._punches)

    for user in users_to_process:
        user_daily_stats = []
        user_punch_data = punches_by_user_day.get(user.id, {'days': {}})
        
        current_date = start_date
        while current_date <= end_date:
            punches_for_day = sorted(
                user_punch_data['days'].get(current_date, []), 
                key=lambda p: p.timestamp, 
                reverse=True
            )
            stats = calculate_daily_attendance(PunchList(punches_for_day))
            user_daily_stats.append({
                'date': current_date,
                'stats': stats,
            })
            current_date += ed.timedelta(days=1)

        report_data.append({
            'user': user,
            'daily_stats': sorted(user_daily_stats, key=lambda x: x['date'], reverse=True)
        })

    context = {
        'report_data': report_data,
        'all_employees': all_employees,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'selected_user_id': int(selected_user_id) if selected_user_id else None,
    }
    return render(request, 'crm/attendance_report.html', context)

from django.shortcuts import render
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.template.loader import render_to_string

def interview_schedule_matrix(request):
    # --- 1. Filter Logic ---
    # Changed default to 'all' if you prefer seeing everything by default, 
    # otherwise keep 'month'.
    date_filter = request.GET.get('date_range', 'month') 
    employee_id = request.GET.get('employee_id')
    
    # Base Query: Only Scheduled or Rescheduled
    queryset = Candidate_Interview.objects.filter(
        status__in=['scheduled', 'rescheduled']
    )

    today = timezone.now().date()
    label = "All Time"

    # Date Filtering
    if date_filter == 'today':
        queryset = queryset.filter(interview_date_time__date=today)
        label = "Today"
    elif date_filter == 'week':
        start_week = today - timedelta(days=today.weekday())
        queryset = queryset.filter(interview_date_time__date__gte=start_week)
        label = "This Week"
    elif date_filter == 'month':
        queryset = queryset.filter(interview_date_time__month=today.month, interview_date_time__year=today.year)
        label = "This Month"
    elif date_filter == 'year':
        queryset = queryset.filter(interview_date_time__year=today.year)
        label = "This Year"
    elif date_filter == 'all':
        # No additional filter - keeps all records
        label = "All Time"

    # Employee Filtering
    if employee_id:
        queryset = queryset.filter(candidate__assigned_to_id=employee_id)

    # --- 2. Prepare Columns (CRITICAL FIX) ---
    # Step A: Get headers from the Vacancy Master Table (The "Expected" columns)
    # Note: We use 'company__company_name' because VacancyDetails links to Company model
    vacancy_headers = set(VacancyDetails.objects.values_list(
        'company__company_name', 'job_profile'
    ))

    # Step B: Get headers from the actual Interview Data (The "Actual" columns)
    # This ensures that if an interview has a typo in company/job name, it still gets a column!
    interview_headers = set(queryset.values_list(
        'company_name', 'job_position'
    ))

    # Step C: Combine them and clean up None values
    # Using a Set Union (|) to remove duplicates
    combined_headers = vacancy_headers | interview_headers
    
    # Clean data: remove entries where company or job is None/Empty
    final_headers = []
    for comp, job in combined_headers:
        if comp and job: # Only add if both exist
            final_headers.append((comp, job))
            
    # Sort alphabetically by Company then Job
    final_headers.sort(key=lambda x: (x[0], x[1]))

    # --- 3. Aggregate Data ---
    stats = queryset.annotate(
        interview_date=TruncDate('interview_date_time')
    ).values(
        'interview_date', 'company_name', 'job_position'
    ).annotate(
        count=Count('id')
    ).order_by('-interview_date')

    # --- 4. Transform Data for Matrix ---
    data_map = {}
    dates_set = set()
    
    for entry in stats:
        d = entry['interview_date']
        if d: # Ensure date is not None
            comp = entry['company_name']
            job = entry['job_position']
            count = entry['count']
            data_map[(d, comp, job)] = count
            dates_set.add(d)

    # Sort dates descending
    sorted_dates = sorted(list(dates_set), reverse=True)

    matrix_rows = []
    # Totals dictionary
    column_totals = {header: 0 for header in final_headers}
    grand_total = 0

    for date_obj in sorted_dates:
        row_counts = []
        for header in final_headers:
            comp_name, job_name = header
            
            # Look up exactly using the header names
            count = data_map.get((date_obj, comp_name, job_name), 0)
            
            row_counts.append({
                'count': count,
                'company': comp_name,
                'job': job_name,
                'date_str': date_obj.strftime('%Y-%m-%d')
            })
            
            column_totals[header] += count
            grand_total += count
        
        matrix_rows.append({
            'date': date_obj,
            'counts': row_counts
        })

    # Convert totals dict to list in order
    footer_counts = [column_totals[h] for h in final_headers]

    context = {
        'vacancy_headers': final_headers, 
        'matrix_rows': matrix_rows,
        'footer_counts': footer_counts,
        'grand_total': grand_total,
        'employees': Employee.objects.all(),
        'selected_date': date_filter,
        'selected_emp': int(employee_id) if employee_id else '',
        'label': label
    }

    return render(request, 'crm/interview_stats.html', context)


# --- HELPER VIEW (No changes needed, but included for completeness) ---
def get_interview_details(request):
    date_str = request.GET.get('date')
    company = request.GET.get('company')
    job = request.GET.get('job')
    
    interviews = Candidate_Interview.objects.filter(
        interview_date_time__date=date_str,
        company_name=company,
        job_position=job,
        status__in=['scheduled', 'rescheduled']
    ).select_related('candidate').order_by('interview_date_time')
    
    html = render_to_string('crm/partials/interview_list_modal.html', {'interviews': interviews})
    return JsonResponse({'html': html})