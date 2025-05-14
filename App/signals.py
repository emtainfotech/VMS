# signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Ticket, TicketActivity

@receiver(post_save, sender=Ticket)
def log_ticket_creation(sender, instance, created, **kwargs):
    if created:
        TicketActivity.objects.create(
            ticket=instance,
            user=instance.created_by,
            action='created',
            comment='Ticket was created'
        )

@receiver(pre_save, sender=Ticket)
def log_ticket_changes(sender, instance, **kwargs):
    if instance.pk:
        original = Ticket.objects.get(pk=instance.pk)
        
        # Track status changes
        if original.ticket_status != instance.ticket_status:
            TicketActivity.objects.create(
                ticket=instance,
                user=instance.updated_by,
                action='status_changed',
                old_value=original.get_ticket_status_display(),
                new_value=instance.get_ticket_status_display()
            )
        
        # Track assignment changes
        if original.ticket_assign_to != instance.ticket_assign_to:
            old_assignee = original.ticket_assign_to.get_full_name() if original.ticket_assign_to else "Unassigned"
            new_assignee = instance.ticket_assign_to.get_full_name() if instance.ticket_assign_to else "Unassigned"
            TicketActivity.objects.create(
                ticket=instance,
                user=instance.updated_by,
                action='assigned',
                old_value=old_assignee,
                new_value=new_assignee
            )