from django.db import models
from django.conf import settings
# Assuming your Employee and Candidate_registration models are in the same app.
# You already have these, so they are not redefined here.
from App.models import Employee, Candidate_registration

class Task(models.Model):
    """
    Represents a task that can be assigned to one or more employees.
    """
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Relationships
    assigned_by = models.ForeignKey(
        Employee, 
        related_name='created_tasks', 
        on_delete=models.SET_NULL, 
        null=True
    )
    assigned_to = models.ManyToManyField(
        Employee, 
        related_name='assigned_tasks',
        blank=True
    )
    candidate = models.ForeignKey(
        Candidate_registration, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='tasks'
    )
    
    # Timestamps
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


class TaskAttachment(models.Model):
    """
    Stores files attached to a specific task.
    """
    task = models.ForeignKey(Task, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='task_attachments/')
    uploaded_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name.split('/')[-1]


class TaskHistory(models.Model):
    """
    Logs all changes and activities related to a task for audit purposes.
    """
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('REASSIGNED', 'Re-assigned'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('PRIORITY_CHANGED', 'Priority Changed'),
        ('COMMENT_ADDED', 'Comment Added'),
    ]

    task = models.ForeignKey(Task, related_name='history', on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(help_text="A description of the change, e.g., 'Changed status from To Do to In Progress'")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.title} - {self.action} by {self.employee}"

    class Meta:
        ordering = ['-timestamp']
