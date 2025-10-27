import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import JobApplication, CourseInquiry, ContactQuery # Make sure to import models

def is_valid_email(email):
    """Simple email regex validation."""
    if not email:
        return False
    # Basic regex for email validation
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)

def is_valid_phone(phone):
    """Validates a 10-digit phone number, as per your HTML."""
    if not phone:
        return False
    # Checks if it contains exactly 10 digits
    regex = r'^\d{10}$'
    return re.match(regex, phone)