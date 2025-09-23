from django.db import models
from django.core.validators import FileExtensionValidator

class ResumeData(models.Model):
    # Basic information fields
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=50)
    sector = models.CharField(max_length=50)

    # Image field for resume image
    resume_image = models.ImageField(
        upload_to='resume_images/', 
        blank=True, 
        null=True
    )

    # File field for resume file, restricted to PDF, DOC, and DOCX formats
    resume_file = models.FileField(
        upload_to='resume_files/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )

    # Edit link field
    edit_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name
    
class CoverData(models.Model):
    # Basic information fields
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=50)
    sector = models.CharField(max_length=50)

    # Image field for resume image
    cover_image = models.ImageField(
        upload_to='cover_images/', 
        blank=True, 
        null=True
    )

    # File field for resume file, restricted to PDF, DOC, and DOCX formats
    cover_file = models.FileField(
        upload_to='cover_files/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )

    # Edit link field
    edit_link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

