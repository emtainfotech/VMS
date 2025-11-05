# from django.db.models.signals import post_save
# from django.dispatch import receiver
# # from .models import Candidate, Notification, Vendor

# @receiver(post_save, sender=Candidate)
# def create_candidate_notification(sender, instance, created, **kwargs):
#     if instance.refer_code and not created:  # Only for updates, not creation
#         vendor = Vendor.objects.filter(refer_code=instance.refer_code).first()
#         if not vendor:
#             return
            
#         if instance.selection_status in ['Selected', 'Rejected']:
#             message = f"Candidate {instance.candidate_name} ({instance.unique_id}) has been {instance.selection_status.lower()}"
#             Notification.objects.create(
#                 vendor=vendor,
#                 message=message,
#                 candidate=instance,
#                 url=f"/candidate/{instance.id}/"
#             )
        
#         if instance.vendor_commission_status in ['Failed', 'Paid']:
#             message = f"Commission for {instance.candidate_name} ({instance.unique_id}) is {instance.vendor_commission_status}"
#             Notification.objects.create(
#                 vendor=vendor,
#                 message=message,
#                 candidate=instance,
#                 url=f"/vendor/commission/{instance.id}/"
#             )