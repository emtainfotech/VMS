# your_app/management/commands/send_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz  # <-- Add this import
from App.models import Candidate_registration, Candidate_Interview, Notification
from CRM.signals import get_recipients

class Command(BaseCommand):
    help = 'Sends scheduled notifications and reminders based on IST.'

    def handle(self, *args, **kwargs):
        ist = pytz.timezone('Asia/Kolkata')
        today_in_ist = timezone.now().astimezone(ist).date()
        
        self.stdout.write(f"[{today_in_ist}] Running reminder command for IST...")

        # Follow-up Date
        candidates_for_followup = Candidate_registration.objects.filter(next_follow_up_date_time__date=today_in_ist)
        for candidate in candidates_for_followup:
            message = f"Follow-up scheduled today for {candidate.candidate_name}."
            recipients = get_recipients(candidate)
            for user in recipients:
                Notification.objects.create(recipient=user, candidate=candidate, message=message, notification_type='follow_up')
        self.stdout.write(f"Found {candidates_for_followup.count()} follow-up reminders.")

        # Candidate Joining Date
        candidates_joining = Candidate_registration.objects.filter(candidate_joining_date=today_in_ist)
        for candidate in candidates_joining:
            message = f"{candidate.candidate_name} is scheduled to join today."
            recipients = get_recipients(candidate)
            for user in recipients:
                Notification.objects.create(recipient=user, candidate=candidate, message=message, notification_type='joining_date')
        self.stdout.write(f"Found {candidates_joining.count()} joining date reminders.")

        # Invoice Date
        candidates_invoice = Candidate_registration.objects.filter(invoice_date=today_in_ist)
        for candidate in candidates_invoice:
            message = f"Invoice is due today for candidate {candidate.candidate_name}."
            recipients = get_recipients(candidate)
            for user in recipients:
                Notification.objects.create(recipient=user, candidate=candidate, message=message, notification_type='invoice_due')
        self.stdout.write(f"Found {candidates_invoice.count()} invoice reminders.")

        # Upcoming Interview Reminder
        interviews_today = Candidate_Interview.objects.filter(interview_date_time__date=today_in_ist)
        for interview in interviews_today:
            interview_time_ist = interview.interview_date_time.astimezone(ist)
            formatted_time = interview_time_ist.strftime('%I:%M %p')
            message = f"Interview reminder: {interview.candidate.candidate_name} at {formatted_time}."
            recipients = get_recipients(interview.candidate)
            for user in recipients:
                Notification.objects.create(recipient=user, candidate=interview.candidate, message=message, notification_type='interview_reminder')
        self.stdout.write(f"Found {interviews_today.count()} interview reminders.")

        self.stdout.write(self.style.SUCCESS('Successfully sent all reminders for IST.'))