# your_app/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from App.models import Candidate_registration, Candidate_Interview, Notification, Employee


# This helper function is still correct and does not need changes
def get_recipients(candidate):
    """Helper function to get the assigned employee and all admins."""
    recipients = set()
    admins = User.objects.filter(is_superuser=True)
    for admin in admins:
        recipients.add(admin)
    if candidate.assigned_to and hasattr(candidate.assigned_to, 'user'):
        recipients.add(candidate.assigned_to.user)
    return list(recipients)

@receiver(pre_save, sender=Candidate_registration)
def create_candidate_notifications(sender, instance, **kwargs):
    """Create notifications by comparing old and new values before the save."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    recipients = get_recipients(instance)
    message = ""
    notification_type = ""

    # 1. Admin remark was added or changed
    if instance.admin_remark and old_instance.admin_remark != instance.admin_remark:
        message = f"An admin remark was added for candidate: {instance.candidate_name}."
        notification_type = 'admin_remark'

    # 2. Candidate was selected
    if instance.selection_status == 'Selected' and old_instance.selection_status != 'Selected':
        message = f"Congratulations! Candidate {instance.candidate_name} has been selected."
        notification_type = 'selection'
        
    if message and recipients:
        for user in recipients:
            Notification.objects.create(
                recipient=user,
                candidate=instance,
                message=message,
                notification_type=notification_type
            )

@receiver(post_save, sender=Candidate_Interview)
def create_interview_notifications(sender, instance, created, **kwargs):
    """
    Create notifications related to Candidate_Interview updates.
    """
    recipients = get_recipients(instance.candidate)
    message = ""

    if created:
        # 3. New interview scheduled
        formatted_time = instance.interview_date_time.strftime('%d-%b-%Y %I:%M %p')
        message = f"New interview scheduled for {instance.candidate.candidate_name} on {formatted_time}."
    else:
        # 4. Interview status changed
        try:
            old_instance = Candidate_Interview.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                message = f"Interview status for {instance.candidate.candidate_name} changed to '{instance.get_status_display()}'."
        except Candidate_Interview.DoesNotExist:
            return

    if message:
        for user in recipients:
            Notification.objects.create(
                recipient=user,
                candidate=instance.candidate,
                message=message
            )