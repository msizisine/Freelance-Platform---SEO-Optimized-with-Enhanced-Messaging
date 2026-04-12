"""
Context processors for global template context
"""
from django.contrib.auth import get_user_model
from messaging.models import Message, MessageNotification

def unread_messages_count(request):
    """
    Add unread messages count to all templates
    """
    if not request.user.is_authenticated:
        return {'unread_count': 0}
    
    try:
        # Count unread message notifications
        unread_notifications = MessageNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        # Also count unread messages in conversations
        from django.db.models import Q, Count
        conversations = request.user.conversations.all().annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
        )
        unread_conversations = sum(conv.unread_count for conv in conversations)
        
        total_unread = unread_notifications + unread_conversations
        
        return {'unread_count': total_unread}
        
    except Exception as e:
        # Fallback to 0 if there's any error
        return {'unread_count': 0}

def user_profile_context(request):
    """
    Add user profile information to all templates
    """
    if not request.user.is_authenticated:
        return {}
    
    return {
        'user_profile': getattr(request.user, 'profile', None),
        'user_first_name': request.user.first_name or request.user.email.split('@')[0]
    }
