from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from App.models import Employee

@receiver(user_logged_in)
def enforce_single_session(sender, request, user, **kwargs):
    """
    Signal receiver to enforce a single active session per user.

    When a user logs in, this function finds and deletes any previously stored
    session key associated with that user, effectively logging them out from
    any other device.
    """
    try:
        # Get the employee profile linked to the logged-in user.
        employee = user.employee
    except Employee.DoesNotExist:
        # If no employee profile exists, we cannot proceed.
        return

    # Store the new session key from the current login request.
    new_session_key = request.session.session_key

    # If an old session key exists and it's different from the new one...
    if employee.active_session_key and employee.active_session_key != new_session_key:
        try:
            # ...find the old session in the database and delete it.
            Session.objects.get(session_key=employee.active_session_key).delete()
        except Session.DoesNotExist:
            # The session might have already expired, which is not an error.
            pass
    
    # Update the employee's record with the new, active session key.
    # We use update_fields for a more efficient database query.
    Employee.objects.filter(pk=employee.pk).update(active_session_key=new_session_key)