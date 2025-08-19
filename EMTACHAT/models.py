# models.py
from django.db import models
from django.contrib.auth.models import User
# Assuming your Employee model is in the same app
from App.models import Employee



class Group(models.Model):
    """
    Represents a chat group.
    Can be a one-on-one chat or a multi-user group.
    """
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(Employee, related_name='chat_groups')
    is_private = models.BooleanField(default=False) # True for one-on-one chats
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='created_groups')

    def __str__(self):
        return self.name

class Message(models.Model):
    """
    Represents a single message within a group.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Employee, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    forwarded_from = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='forwarded_messages')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'Message from {self.sender} in {self.group.name} at {self.timestamp}'

class Attachment(models.Model):
    """
    Represents a file attached to a message.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Attachment for message {self.message.id}'
    


# --- NEW MODELS TO ADD ---
class MessageReadStatus(models.Model):
    """ Tracks when an employee has seen a message. """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'employee')

class EmployeeStatus(models.Model):
    """ Tracks the online status and last seen time of an employee. """
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.first_name} is {'online' if self.is_online else 'offline'}"
