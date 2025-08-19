# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Group, Employee, Attachment, EmployeeStatus, MessageReadStatus

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.employee = await self.get_employee()
        if not self.employee:
            await self.close()
            return

        await self.update_employee_status(self.employee, True)
        await self.broadcast_status_to_groups(True)
        await self.channel_layer.group_add(f"employee_{self.employee.id}", self.channel_name)
        self.user_groups = await self.get_user_groups()
        for group in self.user_groups:
            await self.channel_layer.group_add(f"group_{group.id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'employee') and self.employee:
            await self.update_employee_status(self.employee, False)
            await self.broadcast_status_to_groups(False)
            await self.channel_layer.group_discard(f"employee_{self.employee.id}", self.channel_name)
            if hasattr(self, 'user_groups'):
                for group in self.user_groups:
                    await self.channel_layer.group_discard(f"group_{group.id}", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        handler = getattr(self, f'handle_{message_type}', None)
        if handler:
            await handler(data)

    # --- WebSocket Message Handlers ---
    async def handle_chat_message(self, data):
        message = await self.create_message(data['group_id'], data['message'], data.get('reply_to_id'))
        message_data = await self.format_message(message)
        await self.channel_layer.group_send(f"group_{data['group_id']}", {'type': 'chat.message', 'message': message_data})

    async def handle_forward_message(self, data):
        original_message = await self.get_message_for_forwarding(data['original_message_id'])
        if not original_message: return

        for group_id in data['target_group_ids']:
            forwarded_message = await self.create_forwarded_message(original_message, group_id)
            message_data = await self.format_message(forwarded_message)
            await self.channel_layer.group_send(f"group_{group_id}", {'type': 'chat.message', 'message': message_data})

    async def handle_mark_as_read(self, data):
        await self.mark_message_as_read(data['message_id'], self.employee)
        await self.channel_layer.group_send(f"group_{data['group_id']}", {
            'type': 'message.read', 'message_id': data['message_id'],
            'group_id': data['group_id'], 'reader_id': self.employee.id
        })

    # --- Channel Layer Event Handlers ---
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'new_message', 'message': event['message']}))

    async def message_read(self, event):
        if event['reader_id'] != self.employee.id:
            await self.send(text_data=json.dumps(event))

    async def employee_status_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def group_created(self, event):
        await self.channel_layer.group_add(f"group_{event['group']['id']}", self.channel_name)
        await self.send(text_data=json.dumps(event))

    # --- Helper & DB Methods ---
    async def broadcast_status_to_groups(self, is_online):
        if hasattr(self, 'user_groups'):
            for group in self.user_groups:
                await self.channel_layer.group_send(f"group_{group.id}", {
                    'type': 'employee.status.update', 'employee_id': self.employee.id, 'is_online': is_online
                })

    @database_sync_to_async
    def update_employee_status(self, employee, is_online):
        EmployeeStatus.objects.update_or_create(employee=employee, defaults={'is_online': is_online})

    @database_sync_to_async
    def mark_message_as_read(self, message_id, employee):
        message = Message.objects.get(id=message_id)
        MessageReadStatus.objects.get_or_create(message=message, employee=employee)

    @database_sync_to_async
    def create_message(self, group_id, content, reply_to_id):
        group = Group.objects.get(id=group_id)
        reply_to = Message.objects.get(id=reply_to_id) if reply_to_id else None
        return Message.objects.create(group=group, sender=self.employee, content=content, reply_to=reply_to)

    @database_sync_to_async
    def create_forwarded_message(self, original_message, target_group_id):
        target_group = Group.objects.get(id=target_group_id)
        return Message.objects.create(
            group=target_group, sender=self.employee,
            content=original_message.content, forwarded_from=original_message.sender
        )

    @database_sync_to_async
    def get_message_for_forwarding(self, message_id):
        return Message.objects.select_related('sender').filter(id=message_id).first()

    @database_sync_to_async
    def get_employee(self):
        return Employee.objects.filter(user=self.user).first()

    @database_sync_to_async
    def get_user_groups(self):
        return list(self.employee.chat_groups.all())

    @database_sync_to_async
    def format_message(self, message):
        message = Message.objects.select_related('sender', 'reply_to__sender', 'forwarded_from').prefetch_related('attachments', 'read_by').get(id=message.id)
        reply_to_data = {'sender': message.reply_to.sender.first_name, 'content': message.reply_to.content} if message.reply_to else None
        forwarded_from_data = {'name': f"{message.forwarded_from.first_name} {message.forwarded_from.last_name}"} if message.forwarded_from else None

        return {
            'id': message.id, 'group_id': message.group.id, 'content': message.content,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'sender': {'id': message.sender.id, 'name': message.sender.first_name, 'avatar_url': message.sender.employee_photo.url if message.sender.employee_photo else '/static/images/default_avatar.png'},
            'attachments': [{'id': att.id, 'name': att.file.name.split('/')[-1]} for att in message.attachments.all()],
            'reply_to': reply_to_data, # <<< THIS WAS THE LINE WITH THE TYPO
            'forwarded_from': forwarded_from_data,
            'read_count': message.read_by.count()
        }