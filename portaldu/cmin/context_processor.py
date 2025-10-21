from .models import Notifications, Users

def notifications_processor(request):
    if request.user.is_authenticated and isinstance(request.user, Users):
        unread_notifications = Notifications.objects.filter(user_FK=request.user, is_read=False).order_by('-created_at')[:5]

        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_notifications.count()
        }

    return {'unread_notifications': [], 'unread_count': 0}