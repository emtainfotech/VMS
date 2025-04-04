def notifications(request):
    if request.user.is_authenticated and hasattr(request.user, 'vendor'):
        return {
            'notifications': request.user.vendor.notifications.filter(is_read=False)[:10],
            'unread_count': request.user.vendor.notifications.filter(is_read=False).count()
        }
    return {'notifications': [], 'unread_count': 0}