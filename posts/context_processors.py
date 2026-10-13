from .models import DirectMessage


def unread_messages(request):

    if not request.user.is_authenticated:
        return {
            'unread_messages_count': 0
        }

    count = DirectMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return {
        'unread_messages_count': count
    }