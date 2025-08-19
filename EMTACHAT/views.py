# views.py
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.db.models import Count, Max
from App.models import Employee
from .models import Employee, Group, Message, EmployeeStatus, Attachment
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .consumers import ChatConsumer # We reuse the consumer's message formatter

@login_required
def chat_view(request):
    current_employee = get_object_or_404(Employee, user=request.user)
    conversations = Group.objects.filter(members=current_employee).annotate(
        last_message_time=Max('messages__timestamp')
    ).order_by('-last_message_time')
    all_employees = Employee.objects.exclude(id=current_employee.id)
    context = {
        'current_employee': current_employee,
        'conversations': conversations,
        'all_employees': all_employees,
    }
    return render(request, 'chat/chat.html', context)

@login_required
def get_chat_details(request, group_id):
    current_employee = get_object_or_404(Employee, user=request.user)
    group = get_object_or_404(Group, id=group_id, members=current_employee)
    messages = Message.objects.filter(group=group).select_related('sender', 'reply_to__sender', 'forwarded_from').prefetch_related('attachments', 'read_by').order_by('timestamp')

    consumer_instance = ChatConsumer()
    messages_data = [async_to_sync(consumer_instance.format_message)(msg) for msg in messages]

    other_person_status = None
    if group.is_private:
        other_member = group.members.exclude(id=current_employee.id).first()
        if other_member:
            status, _ = EmployeeStatus.objects.get_or_create(employee=other_member)
            other_person_status = {'name': f"{other_member.first_name} {other_member.last_name}", 'is_online': status.is_online}

    return JsonResponse({
        'messages': messages_data,
        'chat_name': other_person_status['name'] if other_person_status else group.name,
        'chat_status': 'Online' if other_person_status and other_person_status['is_online'] else 'Offline'
    })

@login_required
def create_group_chat(request):
    if request.method == 'POST':
        current_employee = get_object_or_404(Employee, user=request.user)
        data = json.loads(request.body)
        group_name, member_ids = data.get('name'), data.get('members', [])

        if not group_name or not member_ids:
            return JsonResponse({'error': 'Group name and members are required.'}, status=400)

        group = Group.objects.create(name=group_name, created_by=current_employee)
        group.members.add(current_employee)

        channel_layer = get_channel_layer()
        for member_id in member_ids:
            member = get_object_or_404(Employee, id=member_id)
            group.members.add(member)
            async_to_sync(channel_layer.group_send)(
                f"employee_{member.id}",
                {'type': 'group.created', 'group': {'id': group.id, 'name': group.name}}
            )
        return JsonResponse({'status': 'success', 'group_id': group.id})
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def upload_attachment(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        sender = get_object_or_404(Employee, user=request.user)
        file = request.FILES.get('file')

        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        # Create message and attachment, then broadcast it
        message = Message.objects.create(group=group, sender=sender, content=file.name)
        Attachment.objects.create(message=message, file=file)

        channel_layer = get_channel_layer()
        consumer_instance = ChatConsumer()
        message_data = async_to_sync(consumer_instance.format_message)(message)

        async_to_sync(channel_layer.group_send)(
            f"group_{group_id}",
            {'type': 'chat.message', 'message': message_data}
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def download_attachment(request, attachment_id):
    attachment = get_object_or_404(Attachment, id=attachment_id)
    # You can add a security check here to ensure the user is in the group
    return FileResponse(attachment.file.open('rb'), as_attachment=True, filename=attachment.file.name.split('/')[-1])