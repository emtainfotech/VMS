from django import template
import datetime

register = template.Library()

@register.filter
def format_timedelta(value):
    """
    Formats a timedelta object into a HH:MM:SS string.
    """
    if not isinstance(value, datetime.timedelta):
        return value  # Return as-is if it's not a timedelta (e.g., "--")

    total_seconds = int(value.total_seconds())

    # Handle negative times (like for breaks) gracefully, though total_worked should be positive
    if total_seconds < 0:
        is_negative = True
        total_seconds = abs(total_seconds)
    else:
        is_negative = False

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    prefix = "-" if is_negative else ""

    # f-string formats to 02d (e.g., 5 becomes "05")
    return f"{prefix}{hours:02}:{minutes:02}:{seconds:02}"