from App.models import Notification

def notifications(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        return {'notifications': unread_notifications}
    return {}