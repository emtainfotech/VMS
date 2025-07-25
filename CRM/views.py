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
            return redirect("crm_dashboard")  
        else:
            messages.error(request, "Invalid credentials or insufficient permissions.")
    return render(request, "crm/admin-login.html")

def crm_admin_logout(request):
    logout(request)
    return redirect(crm_admin_login)

@login_required
def crm_dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        # Time period filter
        period = request.GET.get('period', 'month')
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
                end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
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
                end_date = (start_date.replace(month=start_date.month+1) 
                        if start_date.month < 12 
                        else start_date.replace(year=start_date.year+1, month=1))
            elif period == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = start_date.replace(year=start_date.year+1)
        
        today_follow_up = timezone.now().date()
        date_range_start = today_follow_up - timedelta(days=2)  # 25th if today_follow_up is 27th
        date_range_end = today_follow_up + timedelta(days=3)    # 30th if today is 27th

        # Get candidates from both databases
        interview_detail_reg = Candidate_Interview.objects.filter(
            interview_date_time__date=today,
            status__in=['Scheduled', 'Rescheduled']
        ).order_by('interview_date_time')
        
        interview_detail_can = EVMS_Candidate_Interview.objects.filter(
            interview_date_time__date=today,
            status__in=['Scheduled', 'Rescheduled']
        ).order_by('interview_date_time')
        
        # Combine both querysets
            # Combine both querysets and sort by register_time (descending)
        interview_detail = list(chain(interview_detail_reg, interview_detail_can))
        interview_detail.sort(key=lambda x: x.interview_date_time if x.interview_date_time else datetime.min.date(), reverse=False)
        
        
        
        # Get candidates from both databases
        follow_up_candidates_reg = Candidate_registration.objects.filter(
            next_follow_up_date_time__isnull=False,
            next_follow_up_date_time__gte=date_range_start,
            next_follow_up_date_time__lte=date_range_end,
            lead_generate='No'
        ).order_by('next_follow_up_date_time')
        
        follow_up_candidates_can = Candidate.objects.filter(
            next_follow_up_date_time__isnull=False,
            next_follow_up_date_time__gte=date_range_start,
            next_follow_up_date_time__lte=date_range_end,
            lead_generate='No'
        ).order_by('next_follow_up_date_time')
        
        # Combine both querysets
            # Combine both querysets and sort by register_time (descending)
        follow_up_candidates = list(chain(follow_up_candidates_reg, follow_up_candidates_can))
        follow_up_candidates.sort(key=lambda x: x.next_follow_up_date_time if x.next_follow_up_date_time else datetime.min.date(), reverse=False)
        


        # Base querysets for both databases
        current_qs_reg = Candidate_registration.objects.all()
        current_qs_can = Candidate.objects.all()
        
        if start_date and end_date:
            current_qs_reg = current_qs_reg.filter(register_time__date__range=[start_date, end_date - timedelta(days=1)])
            current_qs_can = current_qs_can.filter(register_time__date__range=[start_date, end_date - timedelta(days=1)])
        
        # Calculate previous period date ranges for comparison
        prev_day = today - timedelta(days=1)
        prev_week_start = (today - timedelta(days=today.weekday() + 7))
        prev_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        prev_year_start = today.replace(year=today.year-1, month=1, day=1)
        
        # Previous period querysets for both databases
        prev_day_qs_reg = Candidate_registration.objects.filter(register_time__date=prev_day)
        prev_day_qs_can = Candidate.objects.filter(register_time__date=prev_day)
        
        prev_week_qs_reg = Candidate_registration.objects.filter(
            register_time__date__range=[prev_week_start, prev_week_start + timedelta(days=6)])
        prev_week_qs_can = Candidate.objects.filter(
            register_time__date__range=[prev_week_start, prev_week_start + timedelta(days=6)])
        
        prev_month_qs_reg = Candidate_registration.objects.filter(
            register_time__date__range=[prev_month_start, 
                                    (prev_month_start.replace(month=prev_month_start.month+1) 
                                        if prev_month_start.month < 12 
                                        else prev_month_start.replace(year=prev_month_start.year+1, month=1)) - timedelta(days=1)])
        prev_month_qs_can = Candidate.objects.filter(
            register_time__date__range=[prev_month_start, 
                                    (prev_month_start.replace(month=prev_month_start.month+1) 
                                        if prev_month_start.month < 12 
                                        else prev_month_start.replace(year=prev_month_start.year+1, month=1)) - timedelta(days=1)])
        
        prev_year_qs_reg = Candidate_registration.objects.filter(
            register_time__date__range=[prev_year_start, prev_year_start.replace(year=prev_year_start.year+1) - timedelta(days=1)])
        prev_year_qs_can = Candidate.objects.filter(
            register_time__date__range=[prev_year_start, prev_year_start.replace(year=prev_year_start.year+1) - timedelta(days=1)])
        
        # Employee performance metrics for both databases
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
        
        # Combine and deduplicate employee performance data by employee_name
        employee_performance_dict = {}
        for entry in employee_performance_reg + employee_performance_can:
            emp = entry['employee_name']
            if emp not in employee_performance_dict:
                employee_performance_dict[emp] = entry
            else:
                # Sum up the values if duplicate
                employee_performance_dict[emp]['total_candidates'] += entry['total_candidates']
                employee_performance_dict[emp]['selected_candidates'] += entry['selected_candidates']
                employee_performance_dict[emp]['pending_candidates'] += entry['pending_candidates']
                employee_performance_dict[emp]['rejected_candidates'] += entry['rejected_candidates']
        employee_performance = sorted(employee_performance_dict.values(), key=lambda x: x['total_candidates'], reverse=True)

        # Lead generation for both databases
        lead_generation_reg = list(current_qs_reg.filter(lead_generate__in=['Yes', 'Converted']).values('employee_name').annotate(
            lead_count=Count('id')
        ).order_by('-lead_count'))
        
        lead_generation_can = list(current_qs_can.filter(lead_generate__in=['Yes', 'Converted']).values('employee_name').annotate(
            lead_count=Count('id')
        ).order_by('-lead_count'))
        
        # Combine and deduplicate lead generation data by employee_name
        lead_generation_dict = {}
        for entry in lead_generation_reg + lead_generation_can:
            emp = entry['employee_name']
            if emp not in lead_generation_dict:
                lead_generation_dict[emp] = entry
            else:
                lead_generation_dict[emp]['lead_count'] += entry['lead_count']
        lead_generation = sorted(lead_generation_dict.values(), key=lambda x: x['lead_count'], reverse=True)
        
        # Total lead generation
        total_lead_generation = sum([entry['lead_count'] for entry in lead_generation])

        # Call connection status for both databases
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
        
        # Combine and deduplicate call connection data by (employee_name, call_connection)
        call_connection_dict = {}
        for entry in call_connection_reg + call_connection_can:
            key = (entry['employee_name'], entry['call_connection'])
            if key not in call_connection_dict:
                call_connection_dict[key] = entry
            else:
                call_connection_dict[key]['count'] += entry['count']
        call_connection = sorted(call_connection_dict.values(), key=lambda x: (x['employee_name'], -x['count']))

        # Interview status for both databases
        interview_candidates = current_qs_reg.filter(send_for_interview='Yes').count() + current_qs_can.filter(send_for_interview='Yes').count()
        
        # Status counts with comparison percentages
        def get_status_comparison(current_reg, current_can, previous_reg, previous_can):
            current_total = current_reg + current_can
            previous_total = previous_reg + previous_can
            if previous_total > 0:
                change = ((current_total - previous_total) / previous_total) * 100
                return f"{change:+.1f}%"
            elif current_total > 0:
                return "+100%"
            else:
                return "0%"
        
        # Current status for both databases
        current_status_reg = list(current_qs_reg.values('selection_status').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        current_status_can = list(current_qs_can.values('selection_status').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        # Combine and deduplicate current status data by selection_status
        current_status_dict = {}
        for entry in current_status_reg + current_status_can:
            status = entry['selection_status']
            if status not in current_status_dict:
                current_status_dict[status] = entry
            else:
                current_status_dict[status]['count'] += entry['count']
        current_status = sorted(current_status_dict.values(), key=lambda x: -x['count'])
        
        # Status comparison for both databases
        status_comparison = {
            'day': get_status_comparison(
                prev_day_qs_reg.count(), prev_day_qs_can.count(),
                prev_day_qs_reg.count(), prev_day_qs_can.count()
            ),
            'week': get_status_comparison(
                prev_week_qs_reg.count(), prev_week_qs_can.count(),
                prev_week_qs_reg.count(), prev_week_qs_can.count()
            ),
            'month': get_status_comparison(
                prev_month_qs_reg.count(), prev_month_qs_can.count(),
                prev_month_qs_reg.count(), prev_month_qs_can.count()
            ),
            'year': get_status_comparison(
                prev_year_qs_reg.count(), prev_year_qs_can.count(),
                prev_year_qs_reg.count(), prev_year_qs_can.count()
            ),
        }
        
        # Calculate total counts for both databases
        total_candidates = current_qs_reg.count() + current_qs_can.count()
        selected_candidates = (current_qs_reg.filter(selection_status='Selected').count() + 
                             current_qs_can.filter(selection_status='Selected').count())
        pending_candidates = (current_qs_reg.filter(selection_status='Pending').count() + 
                             current_qs_can.filter(selection_status='Pending').count())
        rejected_candidates = (current_qs_reg.filter(selection_status='Rejected').count() + 
                             current_qs_can.filter(selection_status='Rejected').count())
        
        # Previous period counts for both databases
        prev_day_count = prev_day_qs_reg.count() + prev_day_qs_can.count()
        prev_week_count = prev_week_qs_reg.count() + prev_week_qs_can.count()
        prev_month_count = prev_month_qs_reg.count() + prev_month_qs_can.count()
        prev_year_count = prev_year_qs_reg.count() + prev_year_qs_can.count()

        
        
        # Prepare context for template
        context = {
            'employee_performance': employee_performance,
            'lead_generation': lead_generation,
            'total_lead_generation' : total_lead_generation,
            'call_connection': call_connection,
            'interview_candidates': interview_candidates,
            'current_status': current_status,
            'status_comparison': status_comparison,
            'period': period,
            'start_date': start_date,
            'end_date': end_date - timedelta(days=1) if end_date else None,
            'total_candidates': total_candidates,
            'selected_candidates': selected_candidates,
            'pending_candidates': pending_candidates,
            'rejected_candidates': rejected_candidates,
            'prev_day_count': prev_day_count,
            'prev_week_count': prev_week_count,
            'prev_month_count': prev_month_count,
            'prev_year_count': prev_year_count,
            'period': period,
            'start_date': start_date,
            'end_date': end_date - timedelta(days=1) if end_date else None,
            'custom_start': custom_start,
            'custom_end': custom_end,
            'interview_detail': interview_detail,
            'follow_up_candidates': follow_up_candidates,
        }
        return render(request, 'crm/crm-dashboard.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

import datetime as dt
@login_required
def admin_candidate_profile(request, id):
    if request.user.is_staff or request.user.is_superuser:
        candidate = get_object_or_404(Candidate_registration.objects.prefetch_related('activities__employee'), id=id)
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
                'current_salary', 'expected_salary', 'submit_by', 'employee_assigned',
                # Calling Remark
                'call_connection', 'calling_remark', 'lead_generate',
                'send_for_interview', 'next_follow_up_date_time',
                # Selection Record
                'selection_status', 'company_name', 'offered_salary',
                'selection_date', 'candidate_joining_date', 'emta_commission',
                'payout_date', 'selection_remark',
                'other_lead_source', 'other_qualification', 'other_working_status',
                'other_call_connection', 'other_lead_generate',
                'other_interview_status', 'other_selection_status',
                'other_origin_location'
            ]
            
            # Check for changes in all fields
            for field in fields_to_track:
                new_value = request.POST.get(field)
                old_value = getattr(original_candidate, field)
                
                # Convert date objects to string for JSON serialization
                if isinstance(old_value, (dt.date, dt.datetime)):
                    old_value = str(old_value)
                if new_value and field in ['selection_date', 'candidate_joining_date', 'payout_date']:
                    new_value = str(new_value) if new_value else None
                
                if str(old_value) != str(new_value):
                    changes[field] = {
                        'old': old_value,
                        'new': new_value
                    }

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

            if 'submit_all' in request.POST:
                # Get list inputs and convert to string
                preferred_location = request.POST.getlist('preferred_location')
                sector = request.POST.getlist('sector')
                department = request.POST.getlist('department')

                preferred_location_str = ', '.join(preferred_location)
                sector_str = ', '.join(sector)
                department_str = ', '.join(department)

                # Update all fields at once
                candidate.candidate_name = request.POST.get('candidate_name')
                candidate.candidate_mobile_number = request.POST.get('candidate_mobile_number')
                candidate.candidate_email_address = request.POST.get('candidate_email_address')
                candidate.gender = request.POST.get('gender')
                candidate.lead_source = request.POST.get('lead_source')
                candidate.employee_assigned = request.POST.get('employee_assigned')

                if 'candidate_photo' in request.FILES:
                    candidate.candidate_photo = request.FILES['candidate_photo']
                if 'candidate_resume' in request.FILES:
                    candidate.candidate_resume = request.FILES['candidate_resume']

                # Candidate Details
                candidate.candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
                candidate.preferred_location = preferred_location_str
                preferred_state = request.POST.getlist('preferred_state')
                preferred_state_str = ', '.join(preferred_state)
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
                candidate.next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None

                # Selection Record
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

                candidate.updated_by = logged_in_employee
                candidate.save()

                messages.success(request, 'Candidate related details updated successfully!')

            elif 'invoice_releted_data' in request.POST:
                # Handle form submission for invoice details
                candidate.invoice_status = request.POST.get('invoice_status')
                candidate.invoice_date = request.POST.get('invoice_date') or None
                candidate.invoice_amount = request.POST.get('invoice_amount')
                candidate.invoice_remark = request.POST.get('invoice_remark')
                candidate.invoice_paid_status = request.POST.get('invoice_paid_status')
                candidate.invoice_number = request.POST.get('invoice_number')
                # candidate.invoice_attachment = request.FILES.get('invoice_attachment', '')
                candidate.invoice_attachment = request.FILES['invoice_attachment'].name if 'invoice_attachment' in request.FILES else None

                candidate.save()
                messages.success(request, 'Invoice related details updated successfully!')

            # Create activity log if there were changes
            if changes:
                # Convert any remaining date objects to strings
                for field, change in changes.items():
                    if isinstance(change['old'], (dt.date, dt.datetime)):
                        change['old'] = str(change['old'])
                    if isinstance(change['new'], (dt.date, dt.datetime)):
                        change['new'] = str(change['new'])
                
                CandidateActivity.objects.create(
                    candidate=candidate,
                    employee=logged_in_employee,
                    action='updated',
                    changes=changes,
                    remark="Updated via unified form"
                )

            return redirect('admin_candidate_profile', id=id)
        
        
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
            'candidate': candidate,
            'activities': candidate.activities.all().order_by('-timestamp'),
            'today': timezone.now().date(),
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
            'vacancies': vacancies,
            'companies': companies,
            'state': state,
            'state_district': state_district,
            'employees': employees,
        }
            
        return render(request, 'crm/candidate-profile.html', context)
    else:
        return render(request, 'crm/404.html', status=404)  

@login_required    
def admin_candidate_registration(request):
    if request.user.is_staff or request.user.is_superuser:
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
            next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None
            remark = request.POST.get('remark')
            submit_by = request.POST.get('submit_by')
            preferred_location_str = ', '.join(preferred_location)
            sector_str = ', '.join(sector)
            department_str = ', '.join(department)
            
            # Check for duplicates
            duplicate_mobile = Candidate_registration.objects.filter(
                candidate_mobile_number=candidate_mobile_number
            ).exists()
            
            duplicate_email = Candidate_registration.objects.filter(
                candidate_email_address=candidate_email_address
            ).exists()
            
            if duplicate_mobile or duplicate_email:
                errors = []
                if duplicate_mobile:
                    errors.append("Mobile number already registered")
                if duplicate_email:
                    errors.append("Email address already registered")
                return JsonResponse({'status': 'error', 'errors': errors}, status=400)
            
            # Save to database if no duplicates
            Candidate_registration.objects.create(
                employee_name=logged_in_employee,
                candidate_name=candidate_name,
                unique_code=unique_code,
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
            )
            
            return JsonResponse({'status': 'success', 'redirect_url': reverse('admin_candidate_list')})
        
        suggested_unique_code = admin_get_next_unique_code(request)

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
            'suggested_unique_code':suggested_unique_code,
            'districts' : districts,
            'job_sectors' : job_sectors,
            'departments' : departments
        }
        return render (request,'crm/candidate-registration.html',context)    
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)
    
def admin_get_next_unique_code():
    candidate = Candidate_registration.objects.filter(unique_code__regex=r'^EC\d{6}$').values_list('unique_code', flat=True)
    numbers = [int(re.search(r'\d{6}', code).group()) for code in candidate if re.search(r'\d{6}', code)]

    if numbers:
        next_number = max(numbers) + 1  
    else:
        next_number = 1 
    return f"EC{next_number:06d}"


@login_required
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
                            unique_code=row.get('unique_code', admin_get_next_unique_code(request)),
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
    
@login_required 
def admin_candidate_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        candidates_reg = Candidate_registration.objects.all().order_by('-id')
        candidates_can = Candidate.objects.all().order_by('-id')
        
        # Add model type to each candidate for identification
        for candidate in candidates_reg:
            candidate.model_type = 'registration'
        for candidate in candidates_can:
            candidate.model_type = 'candidate'
        
        candidates = list(chain(candidates_reg, candidates_can))
        candidates.sort(key=lambda x: x.register_time, reverse=True)
        
        return render (request,'crm/candidate-list.html',{'candidates':candidates})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
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
    
@login_required   
def admin_company_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        companys = Company_registration.objects.all().order_by('-id')
        return render(request,'crm/company-list.html',{'companys':companys})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
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
                    vacancy.updated_by = request.user
                    
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
        )[:50]
        
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
    
    
@login_required
def admin_vendor_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        vendors = Vendor.objects.all().order_by('-id')
        return render(request,'crm/admin-vendor-list.html',{'vendors':vendors})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
def admin_evms_candidate_list(request) :
    if request.user.is_staff or request.user.is_superuser:
        candidates = Candidate.objects.all().order_by('-id')
        return render(request,'crm/admin-evms-candidate-list.html',{'candidates':candidates})
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
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

@login_required
def evms_candidate_profile(request,id) :
    if request.user.is_staff or request.user.is_superuser:
        candidate = get_object_or_404(Candidate, id=id)
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
            # Store the original candidate data before any updates
            original_candidate = Candidate.objects.get(id=id)
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
                'current_salary', 'expected_salary', 'submit_by', 'employee_assigned',
                # Calling Remark
                'call_connection', 'calling_remark', 'lead_generate',
                'send_for_interview', 'next_follow_up_date_time',
                # Selection Record
                'selection_status', 'company_name', 'offered_salary',
                'selection_date', 'candidate_joining_date', 'emta_commission',
                'payout_date', 'selection_remark',
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
        if request.method == 'POST':
            if 'submit_all' in request.POST:
                # Get list inputs and convert to string
                preferred_location = request.POST.getlist('preferred_location')
                sector = request.POST.getlist('sector')
                department = request.POST.getlist('department')

                preferred_location_str = ', '.join(preferred_location)
                sector_str = ', '.join(sector)
                department_str = ', '.join(department)

                # Handle Employee fields
                candidate.candidate_name = request.POST.get('candidate_name')
                candidate.employee_name = request.POST.get('employee_name')
                candidate.employee_assigned = request.POST.get('employee_assigned')
                candidate.candidate_mobile_number = request.POST.get('candidate_mobile_number')
                candidate.candidate_email_address = request.POST.get('candidate_email_address')
                candidate.gender = request.POST.get('gender')
                candidate.lead_source = request.POST.get('lead_source')
                if 'candidate_photo' in request.FILES:
                    candidate.candidate_photo = request.FILES['candidate_photo']
                if 'candidate_resume' in request.FILES:
                    candidate.candidate_resume = request.FILES['candidate_resume']
                
                # Handle Emergency Contact fields
                candidate.candidate_alternate_mobile_number = request.POST.get('candidate_alternate_mobile_number')
                candidate.preferred_location = preferred_location_str
                preferred_state = request.POST.getlist('preferred_state')
                preferred_state_str = ', '.join(preferred_state)
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

                # Handle Social Media details form submission
                candidate.call_connection = request.POST.get('call_connection')
                candidate.calling_remark = request.POST.get('calling_remark')
                candidate.lead_generate = request.POST.get('lead_generate')
                candidate.send_for_interview = request.POST.get('send_for_interview')
                candidate.next_follow_up_date_time = request.POST.get('next_follow_up_date_time') or None
                
                # Handle form submission for bank details
                candidate.selection_status = request.POST.get('selection_status')
                candidate.company_name = request.POST.get('company_name')
                candidate.job_title = request.POST.get('job_title')
                candidate.offered_salary = request.POST.get('offered_salary')
                candidate.selection_date = request.POST.get('selection_date') or None
                candidate.candidate_joining_date = request.POST.get('candidate_joining_date') or None
                candidate.emta_commission = request.POST.get('emta_commission')
                candidate.payout_date = request.POST.get('payout_date') or None
                candidate.joining_status = request.POST.get('joining_status')
                
                # Handle form submission for bank details
                
                candidate.vendor_commission = request.POST.get('vendor_commission')
                candidate.vendor_payout_date = request.POST.get('vendor_payout_date') or None
                candidate.commission_generation_date = request.POST.get('commission_generation_date') or None
                candidate.vendor_commission_status = request.POST.get('vendor_commission_status')
                candidate.vendor_payment_remark = request.POST.get('vendor_payment_remark')
                candidate.payment_done_by = request.POST.get('payment_done_by')
                candidate.payment_done_by_date = request.POST.get('payment_done_by_date') or None
                if 'submit_recipt' in request.FILES:
                    candidate.submit_recipt = request.FILES['submit_recipt']

                # Handle form submission for invoice details
                candidate.invoice_status = request.POST.get('invoice_status')
                candidate.invoice_date = request.POST.get('invoice_date') or None
                candidate.invoice_amount = request.POST.get('invoice_amount')
                candidate.invoice_remark = request.POST.get('invoice_remark')
                if 'invoice_attachment' in request.FILES:
                    candidate.invoice_attachment = request.FILES['invoice_attachment']

                candidate.other_lead_source = request.POST.get('other_lead_source')
                candidate.other_qualification = request.POST.get('other_qualification')
                candidate.other_working_status = request.POST.get('other_working_status')
                candidate.other_call_connection = request.POST.get('other_call_connection')
                candidate.other_lead_generate = request.POST.get('other_lead_generate')
                candidate.other_interview_status = request.POST.get('other_interview_status')
                candidate.other_selection_status = request.POST.get('other_selection_status')
                candidate.other_origin_location = request.POST.get('other_origin_location')

                

                candidate.save()

                messages.success(request, 'Candidate details updated successfully!')

            elif 'submit_vendor_related_data' in request.POST:
                # Handle form submission for bank details
                candidate.admin_status = request.POST.get('admin_status')
                candidate.vendor_commission = request.POST.get('vendor_commission')
                candidate.vendor_payout_date = request.POST.get('vendor_payout_date') or None
                candidate.commission_generation_date = request.POST.get('commission_generation_date') or None
                candidate.vendor_commission_status = request.POST.get('vendor_commission_status')
                candidate.vendor_payment_remark = request.POST.get('vendor_payment_remark')
                candidate.payment_done_by = request.POST.get('payment_done_by')
                candidate.payment_done_by_date = request.POST.get('payment_done_by_date') or None
                # submit_recipt = request.FILES.get('submit_recipt')
                if 'submit_recipt' in request.FILES:
                    candidate.submit_recipt = request.FILES['submit_recipt']

                candidate.save()

                messages.success(request, 'Vendor related details updated successfully!')

            elif 'invoice_releted_data' in request.POST :
                # Handle form submission for invoice details
                candidate.invoice_status = request.POST.get('invoice_status')
                candidate.invoice_date = request.POST.get('invoice_date') or None
                candidate.invoice_amount = request.POST.get('invoice_amount')
                candidate.invoice_remark = request.POST.get('invoice_remark')
                candidate.invoice_paid_status = request.POST.get('invoice_paid_status')
                candidate.invoice_number = request.POST.get('invoice_number')
                if 'invoice_attachment' in request.FILES:
                    candidate.invoice_attachment = request.FILES['invoice_attachment']
                candidate.save()
                messages.success(request, 'Invoice related details updated successfully!')
                
            return redirect('evms_candidate_profile', id=id)
        
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
            'candidate': candidate,
            'employees' : employees,
            'districts': districts,
            'job_sectors': job_sectors,
            'departments': departments,
            'vacancies': vacancies,
            'activities': candidate.activities.all().order_by('-timestamp'),
            'companies': companies,
            'state': state,
            'state_district': state_district,
        }
        return render(request,'crm/evms-candidate-profile.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
def selected_candidate(request) :
    if request.user.is_staff or request.user.is_superuser:
        logged_in_employee = request.user.employee
        candidates_reg = Candidate_registration.objects.filter(selection_status='Selected').order_by('-id')
        candidates_can = Candidate.objects.filter(selection_status='Selected').order_by('-id')
        candidates = list(chain(candidates_reg, candidates_can))
        candidates.sort(key=lambda x: x.selection_date if x.selection_date else datetime.min.date(), reverse=True)
        context = {
            'candidates': candidates
        }
        return render(request,'crm/selected-candidate.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
def follow_up_candidate(request):
    if request.user.is_staff or request.user.is_superuser:
        today = timezone.now().date()
        date_range_start = today - timedelta(days=2)  # 25th if today is 27th
        date_range_end = today + timedelta(days=3)    # 30th if today is 27th
        
        candidates_reg = Candidate_registration.objects.filter(
            next_follow_up_date_time__isnull=False,
            next_follow_up_date_time__gte=date_range_start,
            next_follow_up_date_time__lte=date_range_end
        ).order_by('next_follow_up_date_time')  # Order by follow-up date

        candidates_can = Candidate.objects.filter(
            next_follow_up_date_time__isnull=False,
            next_follow_up_date_time__gte=date_range_start,
            next_follow_up_date_time__lte=date_range_end
        ).order_by('next_follow_up_date_time')  # Order by follow-up date
        candidates = list(chain(candidates_reg, candidates_can))
        candidates.sort(key=lambda x: x.next_follow_up_date_time if x.next_follow_up_date_time else datetime.min.date(), reverse=False)
        context = {
            'candidates': candidates,
            'today': today
        }
        return render(request, 'crm/follow-up-candidate.html', context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
def generated_leads(request):
    if request.user.is_staff or request.user.is_superuser:
        candidates_reg = Candidate_registration.objects.filter(lead_generate='Yes').order_by('-id')
        candidates_can = Candidate.objects.filter(lead_generate='Yes').order_by('-id')
        candidates = list(chain(candidates_reg, candidates_can))
        candidates.sort(key=lambda x: x.register_time, reverse=True)
        context = {
            'candidates': candidates
        }
        return render(request,'crm/lead-generate.html',context)
    else:
        # If the user is not an admin, show a 404 page
        return render(request, 'crm/404.html', status=404)

@login_required
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

@login_required
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

@login_required
def admin_candidate_chat_list(request, candidate_id):
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

@login_required
def admin_delete_chat(request, pk):
    chat = get_object_or_404(Candidate_chat, pk=pk)
    candidate_id = chat.candidate.id
    chat.delete()
    messages.success(request, 'Chat record deleted successfully!')
    return redirect('admin_candidate_chat_list', candidate_id=candidate_id)

@login_required
def admin_interview_list(request, candidate_id):
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
def admin_interview_detail(request, interview_id):
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

@login_required
def admin_delete_interview(request, interview_id):
    interview = get_object_or_404(Candidate_Interview, id=interview_id)
    candidate_id = interview.candidate.id
    interview.delete()
    messages.success(request, 'Interview deleted successfully!')
    return redirect('admin_interview_list', candidate_id=candidate_id)

@login_required
def admin_company_communication_list(request, company_id):
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

@login_required
def admin_company_communication_detail(request, communication_id):
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

@login_required
def admin_delete_company_communication(request, communication_id):
    communication = get_object_or_404(company_communication, id=communication_id)
    company_id = communication.company.id
    communication.delete()
    messages.success(request, 'Communication record deleted successfully!')
    return redirect('admin_company_communication_list', company_id=company_id)

@login_required
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
    
@login_required
def admin_company_contacts_list(request, company_id):
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

@login_required
def admin_company_contact_detail(request, contact_id):
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

@login_required
def admin_delete_company_contact(request, contact_id):
    contact = get_object_or_404(Company_spoke_person, id=contact_id)
    company_id = contact.company.id
    contact.delete()
    messages.success(request, 'Contact person deleted successfully!')
    return redirect('admin_company_contacts_list', company_id=company_id)

@login_required
def download_candidate_details(request):
    from EVMS.models import Candidate
    from App.models import Candidate_registration
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_candidates.csv"'

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

    crm_candidates = Candidate_registration.objects.all()
    evms_candidates = Candidate.objects.all()

    all_candidates = list(crm_candidates) + list(evms_candidates)
    all_candidates.sort(key=lambda x: x.register_time if x.register_time else datetime.min)

    for obj in all_candidates:
        is_evms = isinstance(obj, Candidate)
        
        # Safely access attributes that might not exist on both models
        unique_code = getattr(obj, 'unique_code', '')
        payout_date = getattr(obj, 'payout_date', '')
        
        # EVMS-specific fields
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

@login_required
def admin_get_next_unique_code(prefix='EMTA'):
    candidate = Candidate_registration.objects.filter(unique_code__regex=r'^EC\d{6}$').values_list('unique_code', flat=True)
    numbers = [int(re.search(r'\d{6}', unique_code).group()) for unique_code in candidate]

    if numbers:
        next_number = max(numbers) + 1  
    else:
        next_number = 1 
    return f"EC{next_number:06d}"

@login_required
def vendor_bank_details(request, vendor_code):
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

@login_required
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

@login_required
def admin_evms_candidate_chat_list(request, candidate_id):
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

@login_required
def admin_evms_delete_chat(request, pk):
    chat = get_object_or_404(EVMS_Candidate_chat, pk=pk)
    candidate_id = chat.candidate.id
    chat.delete()
    messages.success(request, 'Chat record deleted successfully!')
    return redirect('admin_evms_candidate_chat_list', candidate_id=candidate_id)

@login_required
def admin_evms_interview_list(request, candidate_id):
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
def admin_evms_interview_detail(request, interview_id):
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

@login_required
def admin_evms_delete_interview(request, interview_id):
    interview = get_object_or_404(EVMS_Candidate_Interview, id=interview_id)
    candidate_id = interview.candidate.id
    interview.delete()
    messages.success(request, 'Interview deleted successfully!')
    return redirect('admin_evms_interview_list', candidate_id=candidate_id)


from django.core.exceptions import ObjectDoesNotExist

def admin_invoice_list(request):
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
    candidates_reg = Candidate_registration.objects.filter(employee_assigned__isnull=False)
    candidates_can = Candidate.objects.filter(employee_assigned__isnull=False)
    candidates = list(chain(candidates_reg, candidates_can))
    candidates.sort(key=lambda x: x.selection_date or date.min, reverse=True)

    return render(request, 'crm/candidate-assignment.html', { 'candidates' : candidates })